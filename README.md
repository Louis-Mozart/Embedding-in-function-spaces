# functional Embeddings: Embeddings Knowledge Graph in function space

Knowledge graph embedding is successful when using divisional algebras ($\mathbb{R}$, $\mathbb{C}$, $\mathbb{Q}$, etc) as these spaces are helpful to model complex relations and patterns in a KG dataset.  So far, only vectors have been used to compute the embeddings of KGs. This repository aims to extend this idea and
consider another alternative: function space. So we compute and represent the embeddings of entities and relations as functions. First with polynomial functions, then trigonometric and neural network functions. Here we implemented three functional embedding models. The first, called PolyMult, embeds using polynomial functions. The second is called LFMult1 embed using a trigonometric function, and the third is called LFMult embed using Neural Networks. Technical details can be found [here](https://dl.acm.org/doi/10.1145/3627673.3679819)


## Installation
First, make sure you have Anaconda installed
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
First, install all the necessary packages using: 
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
