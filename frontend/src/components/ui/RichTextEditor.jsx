// noinspection JSValidateTypes,JSUnusedGlobalSymbols

import React from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Heading3,
  Code,
  Quote,
  Link as LinkIcon,
  Undo,
  Redo
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from '@/lib/utils';
import { Unlink } from "lucide-react"

// Utility functions
const markdownToHtml = (markdown) => {
  if (!markdown) return '';

  // Handle headers
  let html = markdown
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>');

  // Handle paragraphs
  html = html
    .split(/\n\n+/)
    .map(para => {
      if (para.startsWith('<h')) return para;
      return `<p>${para}</p>`;
    })
    .join('');

  // Handle lists
  html = html
    .replace(/^\* (.*$)/gm, '<li>$1</li>')
    .replace(/<li>.*(?=<li>.*<\/li>)/gs, match => `<ul>${match}`);

  // Handle numbered lists
  html = html
    .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
    .replace(/<li>.*(?=<li>.*<\/li>)/gs, match => `<ol>${match}`);

  // Handle bold and italic
  html = html
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Handle links
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

  // Handle code blocks
  html = html
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');

  // Handle blockquotes
  html = html
    .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');

  return html;
};

const htmlToMarkdown = (html) => {
  if (!html) return '';

  // Create a temporary div to parse HTML
  const div = document.createElement('div');
  div.innerHTML = html;

  // Function to convert a single node
  const convertNode = (node) => {
    if (node.nodeType === 3) { // Text node
      return node.textContent;
    }

    if (node.nodeType !== 1) { // Not an element node
      return '';
    }

    const tag = node.tagName.toLowerCase();
    const children = Array.from(node.childNodes)
      .map(child => convertNode(child))
      .join('');

    switch (tag) {
      case 'h1':
        return `# ${children}\n\n`;
      case 'h2':
        return `## ${children}\n\n`;
      case 'h3':
        return `### ${children}\n\n`;
      case 'p':
        return `${children}\n\n`;
      case 'strong':
      case 'b':
        return `**${children}**`;
      case 'em':
      case 'i':
        return `*${children}*`;
      case 'a':
        return `[${children}](${node.getAttribute('href')})`;
      case 'code':
        const parent = node.parentElement;
        if (parent?.tagName.toLowerCase() === 'pre') {
          return `\`\`\`\n${children}\n\`\`\`\n\n`;
        }
        return `\`${children}\``;
      case 'pre':
        // Skip pre tags as they're handled by code
        return children;
      case 'blockquote':
        return `> ${children}\n\n`;
      case 'ul':
        return children + '\n';
      case 'ol':
        return children + '\n';
      case 'li': {
        const parent = node.parentElement;
        const prefix = parent?.tagName.toLowerCase() === 'ol'
          ? '1. '
          : '* ';
        return `${prefix}${children}\n`;
      }
      case 'br':
        return '\n';
      default:
        return children;
    }
  };

  // Convert all nodes and clean up extra whitespace
  const markdown = convertNode(div);
  return markdown
    .replace(/\n\n\n+/g, '\n\n')
    .trim();
};

const MenuButton = ({ onClick, active, disabled, tooltip, children }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClick}
            disabled={disabled}
            className={cn(
              'h-8 w-8 p-0',
              active && 'bg-accent text-accent-foreground'
            )}
          >
            {children}
          </Button>
        </TooltipTrigger>
        <TooltipContent>{tooltip}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const RichTextEditor = ({ content, onChange, editable = true }) => {
  const [isInternalUpdate, setIsInternalUpdate] = React.useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3]
        }
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-primary underline'
        }
      })
    ],
    editorProps: {
      attributes: {
        class: 'prose max-w-none p-4 focus:outline-none h-[600px] overflow-y-auto'
      }
    },
    content: markdownToHtml(content),
    editable,
    onUpdate: ({ editor }) => {
      setIsInternalUpdate(true);
      const markdown = htmlToMarkdown(editor.getHTML());
      onChange?.(markdown);
      // Reset internal update flag after a short delay
      setTimeout(() => setIsInternalUpdate(false), 10);
    }
  });

  React.useEffect(() => {
    if (!editor || isInternalUpdate) return;

    const currentContent = htmlToMarkdown(editor.getHTML());
    if (currentContent !== content) {
      const html = markdownToHtml(content);
      editor.commands.setContent(html);
    }
  }, [editor, content, isInternalUpdate]);

  if (!editor) {
    return null;
  }

  return (
    <div className="border rounded-md bg-white">
      <div className="border-b p-2 flex flex-wrap gap-1">
        <MenuButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')}
          tooltip="Bold (Ctrl+B)"
        >
          <Bold className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')}
          tooltip="Italic (Ctrl+I)"
        >
          <Italic className="h-4 w-4" />
        </MenuButton>

        <div className="w-px h-6 bg-border mx-1 my-auto" />

        <MenuButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          active={editor.isActive('heading', { level: 1 })}
          tooltip="Heading 1"
        >
          <Heading1 className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          active={editor.isActive('heading', { level: 2 })}
          tooltip="Heading 2"
        >
          <Heading2 className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          active={editor.isActive('heading', { level: 3 })}
          tooltip="Heading 3"
        >
          <Heading3 className="h-4 w-4" />
        </MenuButton>

        <div className="w-px h-6 bg-border mx-1 my-auto" />

        <MenuButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')}
          tooltip="Bullet List"
        >
          <List className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive('orderedList')}
          tooltip="Numbered List"
        >
          <ListOrdered className="h-4 w-4" />
        </MenuButton>

        <div className="w-px h-6 bg-border mx-1 my-auto" />

        <MenuButton
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive('codeBlock')}
          tooltip="Code Block"
        >
          <Code className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive('blockquote')}
          tooltip="Quote"
        >
          <Quote className="h-4 w-4" />
        </MenuButton>

        <div className="w-px h-6 bg-border mx-1 my-auto" />

        <MenuButton
          onClick={() => {
            const url = window.prompt('Enter URL');
            if (url) {
              editor.chain().focus().setLink({ href: url }).run();
            }
          }}
          active={editor.isActive('link')}
          tooltip="Add Link"
        >
          <LinkIcon className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().unsetLink().run()}
          disabled={!editor.isActive('link')}
          tooltip="Remove Link"
        >
          <Unlink className="h-4 w-4" />
        </MenuButton>

        <div className="flex-1" />

        <MenuButton
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          tooltip="Undo"
        >
          <Undo className="h-4 w-4" />
        </MenuButton>

        <MenuButton
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          tooltip="Redo"
        >
          <Redo className="h-4 w-4" />
        </MenuButton>
      </div>

      <EditorContent editor={editor} />
    </div>
  );
};

export default RichTextEditor;