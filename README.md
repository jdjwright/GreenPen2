# GreenPen2

GreenPen is an open-source assessment management suite, which allows teachers and students to view summative, standardised and formative data linked to specificiation points. GreenPen produces detailed analytics of syllabus mastery at the student, cohort and school level.

## Installation

1. Clone this repository with `git clone`
2. If you have not already done so, install [docker](https://www.docker.com/get-started) for your platform.
3. Bring test that the initial setup works correctly with `docker-compose up --build`.
4. Assuming this works correctly, you can now start developing.

## Use with PyCharm

The GreenPen developers use PyCharm as their IDE. To add docker to your PyCharm installation, follow the instructions on the [PyCharm website](https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html)

## First-time setup

1. You can either use docker client to attach a shell to the terminal, or use PyCharm's 'run manage.py' task. Those confident with the use of docker can directly run the following command;
2. Run `manage.py createsueruser` to add yourself as a superuser to the system.

## Contributing

Please feel free to add to the project. It is strongly recommended that you ensure that all code is accompanied by unit tests, and that these all work correclty when running `manage.py test GreenPen`.
