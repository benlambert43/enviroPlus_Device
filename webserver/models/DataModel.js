const mongoose = require('mongoose')

const DataModel = mongoose.Schema({
  date: {
    type: Date,
    default: Date.now
  },
  currentRawTemp: {
    type: String,
    required: true
  },
  currentHumidity: {
    type: String,
    required: true

  },
  currentPressure: {
    type: String,
    required: true

  },
  currentCpuTemp: {
    type: String,
    required: true

  },
  currentAdjustedTemp: {
    type: String,
    required: true

  },
  currentTime: {
    type: String,
    required: true
  }
})

module.exports = mongoose.model('DataModel', DataModel)