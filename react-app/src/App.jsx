import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Gallery from './components/Gallery.jsx';
import Loading from './components/Loading.jsx';
import './App.css';

/**
 * Main App component with routing and layout
 */
export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Gallery />} />
      </Routes>
    </Router>
  );
}