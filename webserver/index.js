const express = require('express')
const app = express();
const mongoose = require('mongoose')
const bodyParser = require('body-parser')
require('dotenv/config')
const uri = process.env.DB_CONNECTION;


app.use(bodyParser.json())
const enviroDataRoute = require('./routes/enviroData')

app.use('/enviroData', enviroDataRoute)

app.get('/', (req, res) => {
  res.send('Server is live.')
})

mongoose.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true }, (err) => (err) ? console.log(err) : console.log("db connected."))

app.listen(4000, '0.0.0.0', () => console.log('Started on port 4000'));