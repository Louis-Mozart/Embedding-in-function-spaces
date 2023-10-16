import argparse
class Namespace(argparse.Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dataset_dir: str = None
        "The path of a folder containing train.txt, and/or valid.txt and/or test.txt"

        self.save_embeddings_as_csv: bool = False
        "A flag for saving embeddings in csv file."

        self.storage_path: str = "Experiments"
        "A directory named with time of execution under --storage_path that contains related data about embeddings."

        self.path_to_store_single_run: str = None
        "A single directory created that contains related data about embeddings."

        self.path_single_kg = None
        "Path of a file corresponding to the input knowledge graph"

        self.sparql_endpoint = None
        "An endpoint of a triple store."

        self.save_embeddings_as_csv=True
        "Embeddings of entities and relations are stored into CSV files to facilitate easy usage."

        self.model: str = "Keci"
        "KGE model"

        self.optim: str = 'Adam'
        "Optimizer"

        self.embedding_dim: int = 64
        "Size of continuous vector representation of an entity/relation"

        self.num_epochs: int = 150
        "Number of pass over the training data"

        self.batch_size: int = 1024
        "Mini-batch size if it is None, an automatic batch finder technique applied"

        self.lr: float = 0.1
        """Learning rate"""

        self.add_noise_rate: float = None
        "The ratio of added random triples into training dataset"

        self.p: int = 0
        "P parameter of Clifford Embeddings"

        self.q: int = 1
        "Q parameter of Clifford Embeddings"

        self.gpus = None
        """Number GPUs to be used during training"""

        self.callbacks = dict()
        """Callbacks, e.g., {"PPE":{ "last_percent_to_consider": 10}}"""

        self.backend: str = "pandas"
        """Backend to read, process, and index input knowledge graph. pandas, polars and rdflib available"""

        self.trainer: str = 'torchCPUTrainer'
        """Trainer for knowledge graph embedding model"""

        self.scoring_technique: str = 'KvsAll'
        """Scoring technique for knowledge graph embedding models"""

        self.neg_ratio: int = 0
        """Negative ratio for a true triple in NegSample training_technique"""

        self.weight_decay: float = 0.0
        """Weight decay for all trainable params"""

        self.input_dropout_rate: float = 0.0
        """Dropout rate on embeddings of input triples"""

        self.hidden_dropout_rate: float = 0.0
        """Dropout rate on hidden representations of  input triples"""

        self.feature_map_dropout_rate: float = 0.0
        """Dropout rate on a feature map generated by a convolution operation"""

        self.normalization: str = "None"
        """ LayerNorm, BatchNorm1d, or None """

        self.init_param: str = None
        """ xavier_normal or None"""

        self.gradient_accumulation_steps: int = 0
        """ Not tested e"""

        self.num_folds_for_cv: int = 0
        """ Number of folds for CV"""

        self.eval_model: str = "train_val_test"
        """ Evaluate trained model choices:["None", "train", "train_val", "train_val_test", "test"]"""

        self.save_model_at_every_epoch: int = None
        """ Not tested """

        self.label_smoothing_rate: float = 0.0

        self.kernel_size: int = 3
        """Size of a square kernel in a convolution operation"""

        self.num_of_output_channels: int = 32
        """Number of slices in the generated feature map by convolution."""

        self.num_core: int = 0
        """Number of CPUs to be used in the mini-batch loading process"""

        self.random_seed: int = 0
        "Random Seed"

        self.sample_triples_ratio: float = None
        """Read some triples that are uniformly at random sampled. Ratio being between 0 and 1"""

        self.read_only_few: int = None
        """Read only first few triples """

        self.pykeen_model_kwargs = dict()
        """Additional keyword arguments for pykeen models"""

    def __iter__(self):
        # Iterate
        for k, v in self.__dict__.items():
            yield k, v
