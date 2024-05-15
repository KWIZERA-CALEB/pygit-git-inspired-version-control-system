import React, {useEffect, useState} from 'react'
import {Routes, Route} from 'react-router-dom'

import AddBook from './Pages/AddBook'
import DeleteBook from './Pages/DeleteBook'
import UpdateBook from './Pages/UpdateBook'
import Home from './Pages/Home'

const App = () => {
  
  return (
    <>
      <Routes>
        <Route path="/" element={<Home />}></Route>
        <Route path="/add" element={<AddBook />}></Route>
        <Route path="/delete/:id" element={<DeleteBook />}></Route>
        <Route path="/update/:id" element={<UpdateBook />}></Route>
      </Routes>
    </>
  )
}

export default App
