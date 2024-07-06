import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to My Kiosk Application</h1>
        <p>Here is the updated content!</p>
        <button onClick={startRecording}>Start Recording</button>
      </header>
    </div>
  );
}

const startRecording = () => {
  // Add your recording logic here
  console.log('Recording started');
};

export default App;
