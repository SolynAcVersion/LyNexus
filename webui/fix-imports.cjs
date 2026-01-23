/**
 * Quick script to fix import paths
 */

const fs = require('fs');
const path = require('path');

const fixes = [
  {
    dir: 'src/components/chat',
    replacements: [
      ["from '@utils'", "from '../../utils'"],
      ["from '@utils/classnames'", "from '../../utils/classnames'"],
      ["from '@types/index'", "from '../../types'"],
      ["from '@types'", "from '../../types'"],
    ]
  },
  {
    dir: 'src/components/common',
    replacements: [
      ["from '@utils/classnames'", "from '../../utils/classnames'"],
    ]
  },
  {
    dir: 'src/components/dialogs',
    replacements: [
      ["from '@utils/classnames'", "from '../../utils/classnames'"],
      ["from '@components/common'", "from '../common'"],
      ["from '@types/index'", "from '../../types'"],
      ["from '@types'", "from '../../types'"],
      ["from '@stores/useAppStore'", "from '../../stores/useAppStore'"],
    ]
  },
  {
    dir: 'src/components/sidebar',
    replacements: [
      ["from '@utils/classnames'", "from '../../utils/classnames'"],
      ["from '@utils'", "from '../../utils'"],
      ["from '@types/index'", "from '../../types'"],
      ["from '@types'", "from '../../types'"],
      ["from '@components/common/Button'", "from '../common/Button'"],
      ["from '@components/chat/MessageList'", "from '../chat/MessageList'"],
      ["from '@components/chat/MessageInput'", "from '../chat/MessageInput'"],
      ["from '@stores/useAppStore'", "from '../../stores/useAppStore'"],
    ]
  },
  {
    dir: 'src/hooks',
    replacements: [
      ["from '@utils'", "from '../utils'"],
      ["from '@types'", "from '../types'"],
    ]
  },
  {
    dir: 'src/stores',
    replacements: [
      ["from '@types/index'", "from '../types'"],
      ["from '@services/api'", "from '../services/api'"],
      ["from '@utils'", "from '../utils'"],
    ]
  },
  {
    dir: 'src',
    replacements: [
      ["from '@components'", "from './components'"],
    ]
  },
];

// Fix lucide-react imports
function fixLucideImports(content) {
  // Replace non-existent Export icon with Download
  content = content.replace(/from 'lucide-react'([^]*import[^,]*,\s*)Export/g, "from 'lucide-react'$1Download");
  return content;
}

function applyFixes() {
  fixes.forEach(({ dir, replacements }) => {
    const fullPath = path.join(__dirname, dir);

    if (!fs.existsSync(fullPath)) {
      console.log(`Skipping ${dir} - not found`);
      return;
    }

    const files = fs.readdirSync(fullPath).filter(f => f.endsWith('.tsx') || f.endsWith('.ts'));

    files.forEach(file => {
      const filePath = path.join(fullPath, file);
      let content = fs.readFileSync(filePath, 'utf-8');

      let changed = false;
      replacements.forEach(([from, to]) => {
        if (content.includes(from)) {
          content = content.split(from).join(to);
          changed = true;
        }
      });

      // Fix lucide imports
      const newContent = fixLucideImports(content);
      if (newContent !== content) {
        content = newContent;
        changed = true;
      }

      if (changed) {
        fs.writeFileSync(filePath, content);
        console.log(`Fixed: ${filePath}`);
      }
    });
  });

  console.log('Done!');
}

applyFixes();
