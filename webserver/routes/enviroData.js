const express = require('express')
const router = express.Router();
const DataModel = require('../models/DataModel')
const fs = require('fs')



router.get('/', (req, res) => {
  res.send('enviroData route.')
})

router.get('/pullAll', async (req, res) => {
  try {
    const allPoints = await DataModel.find()
    res.json(allPoints)
  } catch (err) {
    res.json({ message: err })
  }
})

router.get('/pullDate/:Date', async (req, res) => {
  try {
    const dayData = await importDay(req.params.Date)
    res.json(dayData)
  } catch (err) {
    res.json({ message: err })
  }

})

router.get('/save/:Date', async (req, res) => {
  try {
    exportEOD(req.params.Date)
    res.json(req.params.Date)
  } catch (err) {
    res.json({ message: err })
  }
})

router.get('/:pointID', async (req, res) => {
  try {
    const point = await DataModel.findById(req.params.pointID)
    res.json(point)
  } catch (err) {
    res.json({ message: err })
  }
})

router.delete('/:pointID', async (req, res) => {
  try {
    const deletedPoint = await DataModel.deleteOne({ _id: req.params.pointID })
    res.json(deletedPoint)
  } catch (err) {
    res.json({ message: err })
  }
})

router.delete('/DELETEALL/:deleteDate', async (req, res) => {
  try {
    const deletedAll = await DataModel.deleteMany({ currentDate: req.params.deleteDate })
    res.json(deletedAll)
  } catch (err) {
    res.json({ message: err })
  }
})


const exportEOD = async (day) => {
  try {
    const dayData = await DataModel.find();
    const dataJSON = JSON.stringify(dayData)
    fs.writeFileSync(`./dataStore/${day}.json`, dataJSON)
  } catch (e) {
    return e
  }
}

const importDay = (day) => {
  try {
    const dataBuffer = fs.readFileSync(`./dataStore/${day}.json`)
    const dataJSON = dataBuffer.toString()
    return JSON.parse(dataJSON)
  } catch (e) {
    return []
  }
}



router.post('/', async (req, res) => {
  const dataModel = new DataModel({
    currentPoint: req.body.currentPoint,
    currentRawTemp: req.body.currentRawTemp,
    currentHumidity: req.body.currentHumidity,
    currentPressure: req.body.currentPressure,
    currentCpuTemp: req.body.currentCpuTemp,
    currentAdjustedTemp: req.body.currentAdjustedTemp,
    currentLight: req.body.currentLight,
    currentco2: req.body.currentco2,
    currentno2: req.body.currentno2,
    currentnh3: req.body.currentnh3,
    currentTime: req.body.currentTime,
    currentDate: req.body.currentDate
  })
  try {
    const saved = await dataModel.save()
    res.json(saved)
  } catch (err) {
    res.json(err)
  }
})


module.exports = router