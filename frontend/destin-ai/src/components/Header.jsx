import React from 'react';
import logo from '../assets/logo.png';
import downloadIcon from '../assets/download.png';

const Header = () => {
  const downloadPDF = () => {
    const link = document.createElement('a');
    link.href = '/sample.pdf'; // Replace with actual PDF
    link.download = 'DestinAI_Itinerary.pdf';
    link.click();
  };

  return (
    <header className="header">
      <div className="logo">
        <img src={logo} alt="DestinAI Logo" height="30" />
        <h1>DestinAI</h1>
      </div>
      <button className="download-btn" onClick={downloadPDF}>
        <img src={downloadIcon} alt="Download" height="20" />
      </button>
    </header>
  );
};

export default Header;
