const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

const replacements = {
  '--color-green': '--green',
  '--color-amber': '--amber',
  '--color-red': '--red',
  '--color-blue': '--blue',
  '--color-cyan': '--cyan',
  '--color-indigo': '--indigo',
  '--color-green-transparent': '--green-transparent',
  '--color-amber-transparent': '--amber-transparent',
  '--color-red-transparent': '--red-transparent',
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
