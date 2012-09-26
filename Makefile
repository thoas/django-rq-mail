test:
	flake8 data_exporter --ignore=E501,E127,E128,E124
	coverage run --branch --source=rq_mail manage.py test rq_mail
	coverage report --omit=rq_mail/test*

release:
	python setup.py sdist register upload -s
