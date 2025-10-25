#!/usr/bin/env node
/**
 * Setup API URL from backend port file
 * Run this before starting the frontend to auto-configure API URL
 */

const fs = require('fs');
const path = require('path');

const portFilePath = path.join(__dirname, '..', '..', 'backend', '.port');
const envFilePath = path.join(__dirname, '..', '.env.local');

try {
  if (fs.existsSync(portFilePath)) {
    const port = fs.readFileSync(portFilePath, 'utf-8').trim();
    const apiUrl = `http://localhost:${port}`;
    
    console.log(`✅ Found backend running on port ${port}`);
    console.log(`📡 Setting API URL to: ${apiUrl}`);
    
    // Update or create .env.local
    let envContent = '';
    if (fs.existsSync(envFilePath)) {
      envContent = fs.readFileSync(envFilePath, 'utf-8');
    }
    
    // Remove existing NEXT_PUBLIC_API_URL if present
    envContent = envContent.split('\n')
      .filter(line => !line.startsWith('NEXT_PUBLIC_API_URL='))
      .join('\n');
    
    // Add new API URL
    envContent += `\nNEXT_PUBLIC_API_URL=${apiUrl}\n`;
    
    fs.writeFileSync(envFilePath, envContent.trim() + '\n');
    console.log(`✅ Updated .env.local with API URL`);
  } else {
    console.log('⚠️  Backend .port file not found');
    console.log('💡 Start the backend first: cd ../backend && python3 main.py');
    console.log('📡 Using default API URL: http://localhost:8000');
    
    // Set default URL
    let envContent = '';
    if (fs.existsSync(envFilePath)) {
      envContent = fs.readFileSync(envFilePath, 'utf-8');
    }
    
    envContent = envContent.split('\n')
      .filter(line => !line.startsWith('NEXT_PUBLIC_API_URL='))
      .join('\n');
    
    envContent += `\nNEXT_PUBLIC_API_URL=http://localhost:8000\n`;
    fs.writeFileSync(envFilePath, envContent.trim() + '\n');
  }
} catch (error) {
  console.error('❌ Error setting up API URL:', error.message);
  process.exit(1);
}

