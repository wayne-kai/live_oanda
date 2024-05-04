# old dash app
run:
	python -m venv venv
	. ./venv/bin/activate
	# pip install . 
	pip install waitress
	waitress-serve --host 127.0.0.1 --call app:create_app

# run this to serve both apps
deploy: 
	make -j 2 run-st run-lt

run-st:
	streamlit run main_page.py

run-lt:
	cd live_trading && waitress-serve --host 127.0.0.1 --port 5003 --call app:create_app