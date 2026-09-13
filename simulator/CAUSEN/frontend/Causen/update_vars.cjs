const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

const replacements = {
  '--bg-dark': '--background',
  '--bg-surface': '--surface-secondary', // Overview uses --bg-surface
  '--bg-panel': '--surface',
  '--bg-panel-hover': '--surface-hover',
  '--bg-panel-border': '--border',
  '--text-primary': '--text',
  '--color-primary-bright': '--violet-bright',
  '--color-primary-transparent': '--violet-transparent',
  '--color-primary': '--violet',
};

function processDirectory(directory) {
  const files = fs.readdirSync(directory);
  
  for (const file of files) {
    const fullPath = path.join(directory, file);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      processDirectory(fullPath);
    } else if (fullPath.endsWith('.css') || fullPath.endsWith('.tsx')) {
      let content = fs.readFileSync(fullPath, 'utf8');
      let changed = false;
      
      for (const [oldVar, newVar] of Object.entries(replacements)) {
        if (content.includes(oldVar)) {
          content = content.split(oldVar).join(newVar);
          changed = true;
        }
      }
      
      if (changed) {
        fs.writeFileSync(fullPath, content, 'utf8');
        console.log(`Updated ${fullPath}`);
      }
    }
  }
}

processDirectory(srcDir);
