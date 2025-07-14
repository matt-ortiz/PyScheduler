<template>
  <div ref="editorRef" class="code-editor"></div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { EditorView, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, 
         drawSelection, dropCursor, rectangularSelection, keymap } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { defaultHighlightStyle, syntaxHighlighting, indentOnInput, 
         bracketMatching, foldGutter } from '@codemirror/language'
import { history, indentWithTab, standardKeymap, historyKeymap } from '@codemirror/commands'
import { searchKeymap } from '@codemirror/search'
import { autocompletion, closeBrackets, completionKeymap, 
         closeBracketsKeymap } from '@codemirror/autocomplete'

export default {
  name: 'CodeEditor',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    language: {
      type: String,
      default: 'python' // 'python' or 'text'
    },
    placeholder: {
      type: String,
      default: ''
    },
    readonly: {
      type: Boolean,
      default: false
    },
    lineNumbers: {
      type: Boolean,
      default: true
    },
    darkTheme: {
      type: Boolean,
      default: true
    },
    height: {
      type: String,
      default: 'auto'
    },
    maxHeight: {
      type: String,
      default: '400px'
    }
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    const editorRef = ref(null)
    let editorView = null
    
    const createEditor = async () => {
      if (!editorRef.value) return
      
      // Build comprehensive extensions manually to avoid conflicts
      const extensions = [
        // Core editor features
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightSpecialChars(),
        history(),
        foldGutter(),
        drawSelection(),
        dropCursor(),
        indentOnInput(),
        bracketMatching(),
        closeBrackets(),
        autocompletion(),
        rectangularSelection(),
        
        // Syntax highlighting - this is crucial
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        
        // Keymaps
        keymap.of([
          indentWithTab,
          ...closeBracketsKeymap,
          ...standardKeymap,
          ...searchKeymap,
          ...historyKeymap,
          ...completionKeymap
        ]),
        
        // Update listener
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            const newValue = update.state.doc.toString()
            emit('update:modelValue', newValue)
            emit('change', newValue)
          }
        }),
        
        // Basic styling theme
        EditorView.theme({
          '&': {
            fontSize: '14px',
            fontFamily: "'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace"
          },
          '.cm-editor': {
            minHeight: props.height === 'auto' ? '200px' : props.height,
            maxHeight: props.maxHeight,
            border: '1px solid #d1d5db',
            borderRadius: '6px'
          },
          '.cm-editor.cm-focused': {
            outline: '2px solid #3b82f6',
            outlineOffset: '2px',
            borderColor: '#3b82f6'
          },
          '.cm-content': {
            padding: '12px',
            minHeight: props.height === 'auto' ? '200px' : props.height
          },
          '.cm-gutters': {
            backgroundColor: 'var(--cm-gutter-bg, #f9fafb)',
            borderRight: '1px solid var(--cm-border-color, #e5e7eb)'
          },
          '.cm-lineNumbers .cm-gutterElement': {
            color: 'var(--cm-line-number-color, #6b7280)'
          }
        })
      ]
      
      // Add language support for Python
      if (props.language === 'python') {
        extensions.push(python())
      }
      
      // Add dark theme if enabled
      if (props.darkTheme) {
        extensions.push(oneDark)
        extensions.push(EditorView.theme({
          '.cm-editor': {
            '--cm-bg-color': '#1f2937',
            '--cm-text-color': '#f9fafb',
            '--cm-gutter-bg': '#374151',
            '--cm-border-color': '#4b5563',
            '--cm-line-number-color': '#9ca3af'
          }
        }))
      } else {
        extensions.push(EditorView.theme({
          '.cm-editor': {
            '--cm-bg-color': '#ffffff',
            '--cm-text-color': '#1f2937',
            '--cm-gutter-bg': '#f9fafb',
            '--cm-border-color': '#e5e7eb',
            '--cm-line-number-color': '#6b7280'
          }
        }))
      }
      
      // Configure editor state
      const startState = EditorState.create({
        doc: props.modelValue || '',
        extensions
      })
      
      // Create editor view
      editorView = new EditorView({
        state: startState,
        parent: editorRef.value
      })
      
      // Handle readonly state
      if (props.readonly) {
        editorView.contentDOM.setAttribute('contenteditable', 'false')
      }
    }
    
    const updateContent = (newValue) => {
      if (editorView && newValue !== editorView.state.doc.toString()) {
        editorView.dispatch({
          changes: {
            from: 0,
            to: editorView.state.doc.length,
            insert: newValue || ''
          }
        })
      }
    }
    
    // Watch for value changes from parent
    watch(() => props.modelValue, (newValue) => {
      updateContent(newValue)
    })
    
    // Watch for theme changes
    watch(() => props.darkTheme, async () => {
      if (editorView) {
        editorView.destroy()
        await nextTick()
        createEditor()
      }
    })
    
    onMounted(async () => {
      await nextTick()
      createEditor()
    })
    
    onUnmounted(() => {
      if (editorView) {
        editorView.destroy()
      }
    })
    
    return {
      editorRef
    }
  }
}
</script>

<style scoped>
.code-editor {
  width: 100%;
}

/* Dark mode compatibility */
.dark .code-editor :deep(.cm-editor) {
  --cm-bg-color: #1f2937;
  --cm-text-color: #f9fafb;
  --cm-gutter-bg: #374151;
  --cm-border-color: #4b5563;
  --cm-line-number-color: #9ca3af;
}

/* Light mode compatibility */
.code-editor :deep(.cm-editor) {
  --cm-bg-color: #ffffff;
  --cm-text-color: #1f2937;
  --cm-gutter-bg: #f9fafb;
  --cm-border-color: #e5e7eb;
  --cm-line-number-color: #6b7280;
}
</style>