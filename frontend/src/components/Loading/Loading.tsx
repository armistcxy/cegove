const Loading = () => {
    return (
        <div>
            <div className="w-full bg-white fixed top-[4.7rem] left-0 h-full opacity-70 z-50">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.10.0/css/all.min.css"
                      integrity="sha512-PgQMlq+nqFLV4ylk1gwUOgm6CtIIXkKwaIHp/PAIWHzig/lKZSEGKEysh0TCVbHJXCLN7WetD8TFecIky75ZfQ=="
                      crossOrigin="anonymous" referrerPolicy="no-referrer"/>
                <div className="flex justify-center items-center py-[30vh]">
                    <div className="fas fa-circle-notch fa-spin fa-5x text-blue-700"></div>
                </div>
            </div>
        </div>
    )
}

export default Loading;