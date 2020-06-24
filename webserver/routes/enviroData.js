const express = require('express')
const router = express.Router();
const DataModel = require('../models/DataModel')

router.get('/', (req, res) => {
  res.send('enviroData route.')
})

router.post('/', async (req, res) => {
  const dataModel = new DataModel({
    currentRawTemp: req.body.currentRawTemp,
    currentHumidity: req.body.currentHumidity,
    currentPressure: req.body.currentPressure,
    currentCpuTemp: req.body.currentCpuTemp,
    currentAdjustedTemp: req.body.currentAdjustedTemp,
    currentTime: req.body.currentTime
  })
  try {
    const saved = await dataModel.save()
    res.json(saved)
  } catch (err) {
    res.json(err)
  }
})


module.exports = router