# Momentum Portfolio Manager (MPM)

<!--- These are examples. See https://shields.io for others or to customize this set of shields. You might want to include dependencies, project status and licence info here 
![GitHub repo size](https://img.shields.io/github/repo-size/scottydocs/README-template.md)
![GitHub contributors](https://img.shields.io/github/contributors/scottydocs/README-template.md)--->

MPM is an app that allows users to manage a portfolio of assets using the momentum strategies to target a desired distibution.

You can specify a current portfolio, a target portfolio, a timeframe, frequency of transactions, and moving average strategies in order to compute recommendations on positions.  It also provides a mechanism to back test a scenario.

## Prerequisites

Before you begin, ensure you have met the following requirements:
<!--- These are just example requirements. Add, duplicate or remove as required --->
* You have installed the latest version of `Python 3`, recommended to intall via `pyenv`.
* This project uses `poetry`

For more documentation see: [Poetry Docs](https://python-poetry.org/docs/basic-usage)

## Installing MPM

To install MPM after cloning this repo, follow these steps:

```
poetry init
```
then to install dependencies:
```
poetry install
```

## Using MPM

To use MPM, follow these steps:

```
poetry run pytest tests
```

TODO: Add how to run CLI commands and options

## Contributing to <project_name>
<!--- If your README is long or you have some specific process or steps you want contributors to follow, consider creating a separate CONTRIBUTING.md file--->
To contribute to <project_name>, follow these steps:

1. Fork this repository.
2. Create a branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create the pull request.

Alternatively see the GitHub documentation on [creating a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

## License

This project uses the following license: [MIT License](https://choosealicense.com/licenses/mit/).