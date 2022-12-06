# 1. Create Pytorch-lightning Trainer object from input configuration
import copy
import datetime
import time
import numpy as np
import torch
from pytorch_lightning.callbacks import Callback
from .static_funcs import store_kge, intialize_model
from typing import Optional
import os
import pandas as pd


class AccumulateEpochLossCallback(Callback):
    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def on_fit_end(self, trainer, model):
        # Store into disk
        pd.DataFrame(model.loss_history, columns=['EpochLoss']).to_csv(f'{self.path}/epoch_losses.csv')


class PrintCallback(Callback):
    def __init__(self):
        super().__init__()
        self.start_time = time.time()

    def on_fit_start(self, trainer, pl_module):
        print(pl_module)
        print(pl_module.summarize())
        print("\n[1 / 1] Training is started..")

    def on_fit_end(self, trainer, pl_module):
        training_time = time.time() - self.start_time
        if 60 > training_time:
            message = f'{training_time:.3f} seconds.'
        elif 60 * 60 > training_time > 60:
            message = f'{training_time / 60:.3f} minutes.'
        elif training_time > 60 * 60:
            message = f'{training_time / (60 * 60):.3f} hours.'
        else:
            message = f'{training_time:.3f} seconds.'
        print(f"Done ! It took {message}\n")


class KGESaveCallback(Callback):
    def __init__(self, every_x_epoch: int, max_epochs: int, path: str):
        super().__init__()
        self.every_x_epoch = every_x_epoch
        self.max_epochs = max_epochs
        self.epoch_counter = 0
        self.path = path
        if self.every_x_epoch is None:
            self.every_x_epoch = max(self.max_epochs // 2, 1)

    def on_fit_start(self, trainer, pl_module):
        pass

    def on_epoch_end(self, trainer, pl_module):
        if self.epoch_counter % self.every_x_epoch == 0 and self.epoch_counter > 1:
            print(f'\nStoring model {self.epoch_counter}...')
            store_kge(pl_module,
                      path=self.path + f'/model_at_{str(self.epoch_counter)}_epoch_{str(str(datetime.datetime.now()))}.pt')
        self.epoch_counter += 1


class PseudoLabellingCallback(Callback):
    def __init__(self, data_module, kg, batch_size):
        super().__init__()
        self.data_module = data_module
        self.kg = kg
        self.num_of_epochs = 0
        self.unlabelled_size = len(self.kg.unlabelled_set)
        self.batch_size = batch_size

    def create_random_data(self):
        entities = torch.randint(low=0, high=self.kg.num_entities, size=(self.batch_size, 2))
        relations = torch.randint(low=0, high=self.kg.num_relations, size=(self.batch_size,))
        # unlabelled triples
        return torch.stack((entities[:, 0], relations, entities[:, 1]), dim=1)

    def on_epoch_end(self, trainer, model):
        # Create random triples
        # if trainer.current_epoch < 10:
        #    return None
        # Increase it size, Now we increase it.
        model.eval()
        with torch.no_grad():
            # (1) Create random triples
            # unlabelled_input_batch = self.create_random_data()
            # (2) or use unlabelled batch
            unlabelled_input_batch = self.kg.unlabelled_set[
                torch.randint(low=0, high=self.unlabelled_size, size=(self.batch_size,))]
            # (2) Predict unlabelled batch, and use prediction as pseudo-labels
            pseudo_label = torch.sigmoid(model(unlabelled_input_batch))
            selected_triples = unlabelled_input_batch[pseudo_label >= .90]
        if len(selected_triples) > 0:
            # Update dataset
            self.data_module.train_set_idx = np.concatenate(
                (self.data_module.train_set_idx, selected_triples.detach().numpy()),
                axis=0)
            trainer.train_dataloader = self.data_module.train_dataloader()
            print(f'\tEpoch:{trainer.current_epoch}: Pseudo-labelling\t |D|= {len(self.data_module.train_set_idx)}')
        model.train()


def estimate_q(eps):
    """
    estimate rate of convergence q from sequence esp
    """
    x = np.arange(len(eps) - 1)
    y = np.log(np.abs(np.diff(np.log(eps))))
    line = np.polyfit(x, y, 1)  # fit degree 1 polynomial
    q = np.exp(line[0])  # find q
    return q


def compute_convergence(seq, i):
    assert len(seq) >= i > 0

    return estimate_q(seq[-i:] / (np.arange(i) + 1))


class RelaxCallback(Callback):
    def __init__(self, *, path: str, max_epochs: int):
        super().__init__()
        self.epoch_counter = 0
        self.max_epochs = max_epochs
        self.start_epoch = max_epochs // 2
        self.ma_start_limit = 20
        self.path = path
        self.epoch_losses = []

    def on_fit_start(self, trainer, pl_module):
        pass

    def on_train_epoch_end(self, trainer, model):
        self.epoch_counter += 1
        # (1) Start recording epoch losses
        self.epoch_losses.append(model.loss_history[-1])
        # (3) Check whether we can compute ma 20
        if len(self.epoch_losses) < self.ma_start_limit:
            return
        mva_20 = np.mean(self.epoch_losses[-self.ma_start_limit:])
        mva_10 = np.mean(self.epoch_losses[-self.ma_start_limit//2:])
        mva_5 = np.mean(self.epoch_losses[-self.ma_start_limit//4:])
        last = model.loss_history[-1]

        if mva_5 - last < mva_10 - last < mva_20 - last:
            # We are still going down in the hill
            pass
        else:
            # We see to converge. Start taking snapshots
            print(
                f'SAVE...\t mva_5 - last {mva_5 - last}\tmva_10 - last {mva_10 - last}\tmva_20 - last {mva_20 - last}')
            torch.save(model.state_dict(), f=f"{self.path}/trainer_checkpoint_{str(self.epoch_counter)}.pt")
            # Forget the first epoch loss
            self.epoch_losses.pop()

    def on_fit_end(self, trainer, model):
        """ END:Called """
        print('Perform Averaged on', end='')
        # (1) Set in eval model
        model.eval()
        model.to('cpu')
        last_state = model.state_dict()
        counter = 1.0
        num_models = 0
        # (2) Accumulate weights
        for i in os.listdir(self.path):
            if '.pt' in i:
                num_models += 1
                counter += 1
                for k, v in torch.load(f'{self.path}/{i}', map_location=torch.device('cpu')).items():
                    last_state[k] += v
        # (3) Average (2)
        for k, v in last_state.items():
            if v.dtype != torch.int64:
                last_state[k] /= counter
        # (4) Set (3)
        model.load_state_dict(last_state)
        print(f' {num_models} number of models')


class PolyakCallback(Callback):
    def __init__(self, *, path: str, max_epochs: int, polyak_start_ratio=0.75):
        super().__init__()
        self.epoch_counter = 0
        self.polyak_starts = int(max_epochs * polyak_start_ratio)
        self.path = path

    def on_fit_start(self, trainer, pl_module):
        pass

    def on_train_epoch_end(self, trainer, model):
        if len(model.loss_history) < 20:
            return
        else:
            mva_20 = np.mean(model.loss_history[-20:])
            mva_10 = np.mean(model.loss_history[-10:])
            mva_5 = np.mean(model.loss_history[-5:])
            last = model.loss_history[-1]

            if mva_5 - last < mva_10 - last < mva_20 - last:
                # We are still going down in the hill
                pass
            else:
                # We see to converge. Start taking snapshots
                print('SAVE...')
                torch.save(model.state_dict(), f=f"{self.path}/trainer_checkpoint_{str(self.epoch_counter)}.pt")
                self.epoch_counter += 1
            # (1) Polyak Save Condition
            # if self.epoch_counter > self.polyak_starts:
            #    torch.save(model.state_dict(), f=f"{self.path}/trainer_checkpoint_{str(self.epoch_counter)}.pt")
            # self.epoch_counter += 1

    def on_fit_end(self, trainer, model):
        """ END:Called """
        print('Perform Polyak Averaged on', end='')
        # (1) Set in eval model
        model.eval()
        model.to('cpu')
        last_state = model.state_dict()
        counter = 1.0
        num_models = 0
        # (2) Accumulate weights
        for i in os.listdir(self.path):
            if '.pt' in i:
                num_models += 1
                counter += 1
                for k, v in torch.load(f'{self.path}/{i}', map_location=torch.device('cpu')).items():
                    last_state[k] += v
        # (3) Average (2)
        for k, v in last_state.items():
            if v.dtype != torch.int64:
                last_state[k] /= counter
        # (4) Set (3)
        model.load_state_dict(last_state)
        print(f' {num_models} number of models')


# https://pytorch-lightning.readthedocs.io/en/stable/extensions/callbacks.html#persisting-state
# https://pytorch-lightning.readthedocs.io/en/stable/extensions/callbacks.html#teardown
class AdaptiveKGECallback(Callback):
    def __init__(self):
        super().__init__()

    def setup(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule", stage: Optional[str] = None) -> None:
        pass

    def teardown(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule", stage: Optional[str] = None) -> None:
        pass

    def on_batch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        pass

    def on_epoch_end(self, trainer, model):
        print(trainer.callback_metrics)
