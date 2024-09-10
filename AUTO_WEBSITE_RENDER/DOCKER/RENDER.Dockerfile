FROM node:20.11.0-alpine3.18

RUN apk update

RUN mkdir /opt/node_app && chown node:node /opt/node_app
WORKDIR /opt/node_app

RUN yarn global add nodemon

COPY package.json ./
RUN yarn install --force
ENV PATH /opt/node_app/node_modules/.bin$PATH

COPY . .

RUN mkdir -p /opt/node_app/js/shared
RUN mkdir -p /opt/node_app/css/shared

EXPOSE 8080