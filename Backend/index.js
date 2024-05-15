const express = require('express')
const mongoose = require('mongoose')
const bodyParser = require('body-parser')
const database = require('./database')
const { config } = require('dotenv')
const cors = require('cors')
config()

//require book router
const BookRouter = require('./Routes/Book')

const app = express()

app.use(bodyParser.json())

app.use(cors())


//configure to have access on uploads
app.use('/uploads', express.static('uploads'))


//Callback function to connect to database
database.connect((error) => {
    if(error) {
        console.log('Failed to connect')
    }else{
        app.listen(process.env.APP_PORT, () => {
            console.log(`App conected and running on port ${process.env.APP_PORT}`)

        })
    }
})


app.use('/book', BookRouter)


