FROM python:3.10

RUN pip3 install streamlit==1.38.0 pandas

ADD ./view.py ./view.py
ADD ./prepare.json ./prepare.json
ADD ./.streamlit ./.streamlit/
ADD ./static ./static/

RUN ls

EXPOSE 8501
ENTRYPOINT streamlit run ./view.py prepare.json