# functionnal Embeddings: Embeddings Knowledge Graph in function space

Knowledge graph embedding has shown to be succesfull when using divisional algebras ($\mathbb{R}$, $\mathbb{C}$, $\mathbb{Q}$, etc..) as these space are useful to model complex relations and pattern in a KG dataset.  So far only vectors have been used to computed the ebeddings of KGs. This repository aim to extend this idea and
consider another alternative which is function space. So we compute represent the embeddings of entities and relations as functions. First with polynomial functions then trigonometric and neural network function. Here we implemented three functional embedding model. The first called PolyMult embed using polynomial functions. The second, called LFMult1 embed using trigonometric function and the third called LFMult embed using Neural Networks.


## Installation
First, make sure you have anaconda installed
<details><summary> Click me! </summary>

### Installation from Source
``` bash
conda create -n decal python=3.10.13 --no-default-packages && conda activate decal && cd functionnal-embeddings &&
pip3 install -e .
```

## Download Knowledge Graphs
```bash
wget https://files.dice-research.org/datasets/dice-embeddings/KGs.zip --no-check-certificate && unzip KGs.zip
```

</details>

## Knowledge Graph Embedding Models
<details> <summary> To see available Models</summary>

1. TransE, DistMult, ComplEx, ConEx, QMult, OMult, ConvO, ConvQ, PolyMult, LFMult, FMult, LFMult1

</details>

# How to use this repo?
First install all the necessary packages using: 
```bash
 pip install -r requirements.txt 
 ```

### Embedding with polynomials: 
To get the results obtained in the paper for the UMLS data, do:

```bash
python3 run.py --model PolyMult --eval_model "train_val_test" --scoring_technique NegSample --degree 1 --lr 0.02 --embedding_dim 32 --num_epochs 500 --neg_ratio 50 --optim Adam --batch_size 1024
```

### Embedding with trigonometric function:
```bash
python3 run.py --model LFMult1 --eval_model "train_val_test" --scoring_technique NegSample --degree 1 --lr 0.02 --embedding_dim 32 --num_epochs 500 --neg_ratio 50 --optim Adam --batch_size 1024
```
### Embedding with Neural Networks:
```bash
python3 run.py --model LFMult1 --eval_model "train_val_test" --scoring_technique NegSample --degree 1 --lr 0.02 --embedding_dim 32 --num_epochs 500 --neg_ratio 50 --optim Adam --batch_size 1024
```
