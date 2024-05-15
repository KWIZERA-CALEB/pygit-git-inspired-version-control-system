const mongoose = require('mongoose')
const Schema = mongoose.Schema

const BookSchema = new Schema({
    book_name: {
        type: String
    },
    author: {
        type: String
    },
    description: {
        type: String
    },
    image: {
        type: String
    }
}, {timestamps: true})

const Book = mongoose.model('Book', BookSchema)

module.exports = Book