## Update and Upgrade kerner
FROM python:3.8
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install libsqlite3-dev sqlite3 tini
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR src/
RUN sqlite3 -batch "quiz.sqlite" <"quiz.sql"

RUN python3 adduser.py
# RUN python3 softdes.py
ENTRYPOINT [ "python" ]
CMD ["softdes.py"]
# EXPOSE 5001
