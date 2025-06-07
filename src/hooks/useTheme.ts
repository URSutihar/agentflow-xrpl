import { useState, useEffect } from 'react';

export const useTheme = () => {
  // Initialize from localStorage or default to dark mode
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : true;
  });

  // Update localStorage and document class when theme changes
  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    document.documentElement.classList.toggle('light-theme', !isDarkMode);
  }, [isDarkMode]);

  // Set initial theme on first load
  useEffect(() => {
    document.documentElement.classList.toggle('light-theme', !isDarkMode);
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return { isDarkMode, toggleTheme };
}; 