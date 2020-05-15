# Getting started

## Create a Project
The best way to start using STACKn is by creating a new Project. To do so, 
follow the steps below:

1. Click `Projects` in the side menu to the left.
2. Type in a name and description for your Project.
3. If you have an existing GitHub repository that you want to use as a base
for your Project, include a URL to it in the `Import from...` field.

## Project Overview
Once you have created a Project, you will see another side menu that gives you
access to the different components of STACKn. In the `Overview` page, you will see
a README.md file content which is taken from the GitHub repository that you have 
imported when creating the project. Otherwise, you will see a __Getting Started__ 
guide similar to this one.

## Create a new Lab Session
Lab Sessions take important part in your Projects. To set one up, follow the steps below:

1. Go to `Labs` from the side menu to the left.
2. Choose an `Image` and a `Flavor` for you Lab Session.
3. Simply press `Submit`. 

You will see a list of your Lab Sessions below the submit form.

![Lab Sessions](https://github.com/scaleoutsystems/stackn/tree/master/docs/images/labs.png)

## Datasets
When you create a Project, you automatically get an S3 storage created for your datasets, 
reports, models etc. You can control what is available in your `datasets` bucket 
directly from STACKn in the `Datasets` page.

On top of the page, you can find a link to your MinIO instance together with the login
credentials. Once you are logged in, you can upload files and manage your buckets, but 
do not delete or rename the already existing buckets.

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

