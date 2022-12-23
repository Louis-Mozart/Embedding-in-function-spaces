import os
import time
from typing import List, Tuple
import pandas as pd
import torch
from torch import optim
from torch.utils.data import DataLoader
from .abstracts import BaseInteractiveKGE
from .dataset_classes import TriplePredictionDataset
from tqdm import tqdm


class KGE(BaseInteractiveKGE):
    """ Knowledge Graph Embedding Class for interactive usage of pre-trained models"""

    # @TODO: we can download the model if it is not present locally
    def __init__(self, path_of_pretrained_model_dir, construct_ensemble=False, model_name=None,
                 apply_semantic_constraint=False):
        super().__init__(path_of_pretrained_model_dir, construct_ensemble=construct_ensemble, model_name=model_name,
                         apply_semantic_constraint=apply_semantic_constraint)

    def predict_conjunctive_query(self, entity: str, relations: list, k):
        """ Return m given (a,r,b) \land (b,r_i,c) ... (c,r_k,m)  """
        assert isinstance(entity, str)
        assert isinstance(relations, list)
        assert len(entity) >= 1
        assert len(relations) >= 1

        results = {entity}
        # Iterate over relations
        while relations:
            r = relations.pop(0)

            tail_entities = set()
            # Iterative over entities
            while results:
                e = results.pop()
                # answers =: topK(f(e,r,?))
                _, str_tail_entities = self.predict_topk(head_entity=[e], relation=[r], k=k)

                if isinstance(str_tail_entities,str):
                    tail_entities.add(str_tail_entities)
                else:
                    tail_entities.update(set(str_tail_entities))
            # Accumulate results
            results.update(tail_entities)

        return results

    def find_missing_triples(self, confidence: float, top: int = 10) -> set:
        assert 1.0 >= confidence >= 0.0
        assert top >= 1

        # (2) Get entities
        entities = self.entity_to_idx.index.to_list()
        # (3) Get relations
        relations = self.relation_to_idx.index.to_list()
        # (4) A set of inferred triples
        extended_triples = set()
        print(f'Number of entities:{len(entities)} \t Number of relations:{len(relations)}')
        # (5) Cartesian Product over entities and relations
        # (5.1) Iterate over entities
        print('Finding missing triples..')
        for str_head_entity in (pbar := tqdm(entities)):
            idx_entity = entities.index(str_head_entity)
            # (5.1) Iterate over relations
            for str_relation in relations:
                # (5.2) \forall e \in Entities store a tuple of scoring_func(head,relation,e) and e
                # (5.3.) Sort (5.2) and return top  tuples
                predicted_scores, str_tail_entities = self.predict_topk(head_entity=[str_head_entity],
                                                                        relation=[str_relation],
                                                                        k=top)
                # (5.4) Iterate over 5.3
                for predicted_score, str_entity in zip(predicted_scores, str_tail_entities):
                    # (5.5) If score is less than 99% ignore it
                    if predicted_score < confidence:
                        break
                    else:
                        # (5.6) Check whether this triple exists in KG
                        idx_relation = relations.index(str_relation)
                        # False if 0, otherwise 1
                        is_in = bool(
                            len(self.train_set[(self.train_set["subject"] == idx_entity) &
                                               (self.train_set["relation"] == idx_relation) &
                                               (self.train_set["object"] == entities.index(
                                                   str_entity))]))
                        # (5.7) If (5.6) is true, ignore it
                        if is_in:
                            continue
                        else:
                            # (5.8) Remember it
                            # n_triple = f"<{str_head_entity}>\t<{str_relation}>\t<{str_entity}>\t.\n"
                            # print(n_triple)
                            extended_triples.add((str_head_entity, str_relation, str_entity))
                            pbar.set_description_str(f'Number of found missing triples: {len(extended_triples)}')

        return extended_triples

    def construct_input_and_output(self, head_entity: List[str], relation: List[str], tail_entity: List[str], labels):
        """
        Construct a data point
        :param head_entity:
        :param relation:
        :param tail_entity:
        :param labels:
        :return:
        """
        idx_head_entity, idx_relation, idx_tail_entity = self.index_triple(head_entity, relation, tail_entity)
        x = torch.hstack((idx_head_entity, idx_relation, idx_tail_entity))
        # Hard Labels
        labels: object = torch.FloatTensor(labels)
        return x, labels

    def train_cbd(self, head_entity, iteration=1, lr=.01, batch_size: int = None, neg_sample_ratio: int = 1,
                  num_workers: int = os.cpu_count()):
        """
        Train/Retrain model via applying KvsAll training/scoring technique on CBD of an head entity

        Given a head_entity,
        1) Build {r | (h r x) \in G)
        2) Build x:=(h,r), y=[0.....,1]
        3) Construct (2) as a batch
        4) Train
        """
        start_time = time.time()
        assert len(head_entity) == 1
        # (1) Get integer index of head entity.
        try:
            idx_head_entity = self.entity_to_idx.loc[head_entity]['entity'].values[0]
        except KeyError as e:
            print(f'Exception:\t {str(e)}')
            return

        print(f'\nExtracting relevant relations for training from CBD of {head_entity[0]}...')
        # (2) Select triples that (1) occur in.
        triples: pd.DataFrame
        triples = self.train_set[self.train_set['subject'] == idx_head_entity].values
        print(f'Frequency of {head_entity} = {len(triples)}', end='\t')

        # (3) create labels
        if batch_size is None:
            batch_size = max(len(triples) // 10, 1)

        train_set = TriplePredictionDataset(triples,
                                            num_entities=self.num_entities,
                                            num_relations=self.num_relations, neg_sample_ratio=neg_sample_ratio)
        del triples
        data_loader = DataLoader(train_set,
                                 batch_size=batch_size,
                                 num_workers=num_workers,
                                 collate_fn=train_set.collate_fn)

        # (4) Train
        self.set_model_train_mode()
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=.00001)
        print('\nIteration starts.')

        for epoch in range(iteration):
            epoch_loss = 0
            for x, y in data_loader:
                optimizer.zero_grad()
                outputs = self.model(x)
                loss = self.model.loss(outputs, y)
                epoch_loss += loss.item()
                loss.backward()
                optimizer.step()
            print(f"Iteration:{epoch}\t Loss:{epoch_loss:.10f}")
        self.set_model_eval_mode()
        print(f'Online Training took {time.time() - start_time:.4f} seconds.')

    def train_triples(self, head_entity: List[str], relation: List[str], tail_entity: List[str], labels: List[float],
                      iteration=2, lr=.1):
        """

        :param head_entity:
        :param relation:
        :param tail_entity:
        :param labels:
        :param iteration:
        :param lr:
        :return:
        """
        assert len(head_entity) == len(relation) == len(tail_entity) == len(labels)
        # (1) From List of strings to TorchLongTensor.
        x = torch.LongTensor(self.index_triple(head_entity, relation, tail_entity)).reshape(1, 3)
        # (2) From List of float to Torch Tensor.
        labels = torch.FloatTensor(labels)
        # (3) Train mode.
        self.set_model_train_mode()
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=.00001)
        print(f'Iteration starts...')
        # (4) Train.
        for epoch in range(iteration):
            optimizer.zero_grad()
            outputs = self.model(x)
            loss = self.model.loss(outputs, labels)
            print(f"Iteration:{epoch}\t Loss:{loss.item()}\t Outputs:{outputs.detach().mean()}")
            loss.backward()
            optimizer.step()
        # (5) Eval
        self.set_model_eval_mode()
        with torch.no_grad():
            outputs = self.model(x)
            loss = self.model.loss(outputs, labels)
            print(f"Eval Mode:\tLoss:{loss.item()}")

    def train_k_vs_all(self, head_entity, relation, iteration=1, lr=.001):
        """
        Train k vs all
        :param head_entity:
        :param relation:
        :param iteration:
        :param lr:
        :return:
        """
        assert len(head_entity) == 1
        # (1) Construct input and output
        out = self.construct_input_and_output_k_vs_all(head_entity, relation)
        if out is None:
            return
        x, labels, idx_tails = out
        # (2) Train mode
        self.set_model_train_mode()
        # (3) Initialize optimizer # SGD considerably faster than ADAM.
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=.00001)

        print('\nIteration starts.')
        # (3) Iterative training.
        for epoch in range(iteration):
            optimizer.zero_grad()
            outputs = self.model(x)
            loss = self.model.loss(outputs, labels)
            if len(idx_tails) > 0:
                print(
                    f"Iteration:{epoch}\t Loss:{loss.item()}\t Avg. Logits for correct tails: {outputs[0, idx_tails].flatten().mean().detach()}")
            else:
                print(
                    f"Iteration:{epoch}\t Loss:{loss.item()}\t Avg. Logits for all negatives: {outputs[0].flatten().mean().detach()}")

            loss.backward()
            optimizer.step()
            if loss.item() < .00001:
                print(f'loss is {loss.item():.3f}. Converged !!!')
                break
        # (4) Eval mode
        self.set_model_eval_mode()
        with torch.no_grad():
            outputs = self.model(x)
            loss = self.model.loss(outputs, labels)
        print(f"Eval Mode:Loss:{loss.item():.4f}\t Outputs:{outputs[0, idx_tails].flatten().detach()}\n")

    def train(self, kg, lr=.1, epoch=10, batch_size=32, neg_sample_ratio=10, num_workers=1) -> None:
        """ Retrained a pretrain model on an input KG via negative sampling."""
        # (1) Create Negative Sampling Setting for training
        print('Creating Dataset...')
        train_set = TriplePredictionDataset(kg.train_set,
                                            num_entities=len(kg.entity_to_idx),
                                            num_relations=len(kg.relation_to_idx),
                                            neg_sample_ratio=neg_sample_ratio)
        num_data_point = len(train_set)
        print('Number of data points: ', num_data_point)
        train_dataloader = DataLoader(train_set, batch_size=batch_size,
                                      #  shuffle => to have the data reshuffled at every epoc
                                      shuffle=True, num_workers=num_workers,
                                      collate_fn=train_set.collate_fn, pin_memory=True)

        # (2) Go through valid triples + corrupted triples and compute scores.
        # Average loss per triple is stored. This will be used  to indicate whether we learned something.
        print('First Eval..')
        self.set_model_eval_mode()
        first_avg_loss_per_triple = 0
        for x, y in train_dataloader:
            pred = self.model(x)
            first_avg_loss_per_triple += self.model.loss(pred, y)
        first_avg_loss_per_triple /= num_data_point
        print(first_avg_loss_per_triple)
        # (3) Prepare Model for Training
        self.set_model_train_mode()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        print('Training Starts...')
        for epoch in range(epoch):  # loop over the dataset multiple times
            epoch_loss = 0
            for x, y in train_dataloader:
                # zero the parameter gradients
                optimizer.zero_grad()
                # forward + backward + optimize
                outputs = self.model(x)
                loss = self.model.loss(outputs, y)
                epoch_loss += loss.item()
                loss.backward()
                optimizer.step()
            print(f'Epoch={epoch}\t Avg. Loss per epoch: {epoch_loss / num_data_point:.3f}')
        # (5) Prepare For Saving
        self.set_model_eval_mode()
        print('Eval starts...')
        # (6) Eval model on training data to check how much an Improvement
        last_avg_loss_per_triple = 0
        for x, y in train_dataloader:
            pred = self.model(x)
            last_avg_loss_per_triple += self.model.loss(pred, y)
        last_avg_loss_per_triple /= len(train_set)
        print(f'On average Improvement: {first_avg_loss_per_triple - last_avg_loss_per_triple:.3f}')
