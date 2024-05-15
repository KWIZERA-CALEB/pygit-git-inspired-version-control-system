import React from 'react'

const Spinner = () => {
  return (
    <div className='flex justify-center items-center'>
      <div className='w-[40px] h-[40px] rounded-[50%] animate-ping bg-blue-500 p-[10px]'></div>
    </div>
  )
}

export default Spinner
