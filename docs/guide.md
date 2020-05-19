# Getting started

## Create a Project
To get up and running with STACKn, start by creating a new Project 
following the steps below:

1. Click `Projects` in the left side menu.
2. Type in a name and description for your Project.
3. If you have an existing GitHub repository that you want to use as a base
for your Project, include a URL to it in the `Import from...` field. This will import the repository in your Project file area.

## Project Overview
Once you have created a Project, you will see another side menu that gives you
access to the different components of STACKn. On the `Overview` page, you will see
a README.md file that serves as an introduction to the project. It's content is taken from a README file in the root of your working directory. If no such file is present, you will see a __Getting Started__ 
guide similar to this one.

## Create a new Lab Session
Lab Sessions let you spawn Jupyter Labs instances backed by resources of a given flavor. Labs are the hub for experimentation in your Projects. To set one up, follow the steps below:

1. Go to `Labs` from the side menu to the left.
2. Choose an `Image` and a `Flavor` for you Lab Session.
3. Simply press `Submit`. 

You will see a list of your Lab Sessions below the submit form.

![Lab Sessions](https://github.com/scaleoutsystems/stackn/tree/master/docs/images/labs.png)

## Datasets
When you create a Project, you automatically get an S3-compatible object storage (MinIO) for your datasets, 
reports, models etc. You can see what is available in your `datasets` bucket 
directly from STACKn on the `Datasets` page.

On top of the page, you find a link to your MinIO instance together with the login
credentials. Once you are logged in, you can upload files and manage your buckets, but 
do not delete or rename the already existing buckets since they fill specific functions.

![Datasets](https://github.com/scaleoutsystems/stackn/tree/master/docs/images/datasets.png)

## Models
You can see a list of your machine learning models on the `Models` page. From there, 
you can also deploy models or delete the ones that are not needed anymore.

## Metrics
Within the `Metrics` page, you can see a list of all your configurations for measuring
a model's performance. For example, classification reports.

To add new Metrics, click `Add new` in the top right corner of the screen.

![Add Metrics](https://github.com/scaleoutsystems/stackn/tree/master/docs/images/metrics.png)

To be able to configure this, you need to have a file implementing the algorithm for 
measuring the performance of the model. We call this a `generator file`. You might want 
to set up a way to visualize this performance. For example, a pyplot for a classification
report. We call this a `visualizer file`. These two files and any other metrics-related files
need to be placed under a folder called `reports` in your Lab Session. In this way, you will
get access to all the related files within your working directory when executing the generation
and visualization algorithms. Once the files are stored in the correct place, you will see 
them in the drop-down menus in the submit form.

## Settings
The `Settings` page contains all the information about your Project and its components. Some
of the things you can do there are:

- Change your Project's description
- Find link to your MinIO instance and login keys
- Download a configuration file for your Project which is required when working with 
STACKn CLI
- Transfer ownership of your Project to another user
- Delete permanently your Project

## Next steps
Now that you are familiar with the base functionality of STACKn, a good next step is to work through the example Projects available here: 

* [Classification of hand-written digits (MNIST)](https://github.com/scaleoutsystems/digits-example-project)
* [Classfication of malignant blood cells (AML)](https://github.com/scaleoutsystems/aml-example-project)

These examples will teach you how to build a ML-model from scratch and how to serve it for private or public use. 
