const express = require('express')
const mongoose = require('mongoose')

const db_name = 'book_store'
const db_url = `mongodb://127.0.0.1:27017/${db_name}`

const connect = function(cb) {
    mongoose.connect(db_url)
        .then((response) => {
            console.log('Database connected')
            cb()
        })
        .catch((error) => {
            console.log(error)
            cb()
        })
}

module.exports = {connect}