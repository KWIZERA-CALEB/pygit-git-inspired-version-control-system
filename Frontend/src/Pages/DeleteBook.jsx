import React, {useState} from 'react'
import axios from 'axios'
import Spinner from '../Components/Spinner'
import { useNavigate, useParams } from 'react-router-dom'

const DeleteBook = () => {
  const [loading, setLoading] = React.useState(false)
  const navigate = useNavigate()
  const { id } = useParams()

  //delete book function
  const HandleDeleteBook = ()=> {
      setLoading(true)
      axios
        .delete(`http://localhost:5000/book/destroy/${id}`)
          .then(()=> {
            setLoading(false)
            navigate('/')
          })
          .catch((error)=> {
            console.log(error)
            setLoading(false)
          })
  }
  return (
    <div>
      {loading ? <Spinner /> : ''}
      <button className='bg-red-500 text-white rounded-[10px] p-[10px]' onClick={HandleDeleteBook}>Delete</button>
    </div>
  )
}

export default DeleteBook
