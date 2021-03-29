FROM python:3

WORKDIR /usr/src/candy_delivery_app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

COPY . .

CMD [ "python", "init.py" ]