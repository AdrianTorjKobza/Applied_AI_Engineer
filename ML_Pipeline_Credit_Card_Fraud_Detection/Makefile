install:
	pip install -r requirements.txt

train:
	python pipeline.py

serve:
	uvicorn src.serving.api:app --reload

mlflow:
	mlflow ui

docker:
	docker-compose up --build