const express = require('express')
const router = express.Router()

const BookController = require('../Controllers/Book')

//Upload file middleware
const Upload = require('../Middlewares/Upload')

router.get('/', BookController.index)
router.post('/add', Upload.single('image'), BookController.store)
router.put('/update/:id', BookController.update)
router.get('/show/:id', BookController.show)
router.get('/single/:id', BookController.single)
router.delete('/destroy/:id', BookController.destroy)

module.exports = router