import React from 'react';
import { Check, X, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import RichTextEditor from '@/components/ui/RichTextEditor';

// Did You Know generator dialog
export const GenerateDYKDialog = ({
  isOpen,
  onClose,
  onGenerate,
  defaultCount = 3
}) => {
  const [count, setCount] = React.useState(defaultCount);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Generate "Did You Know?" Posts</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="count">Number of Posts</Label>
            <Input
              id="count"
              type="number"
              min="1"
              max="10"
              value={count}
              onChange={(e) => {
                const value = Math.max(1, Math.min(10, parseInt(e.target.value) || 1));
                setCount(value);
              }}
            />
            <p className="text-sm text-muted-foreground">
              Choose between 1 and 10 posts
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => onGenerate?.(count)}>
            Generate
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const TagsSelect = ({ tags, selectedTagIds = [], onChange }) => {
  // Make sure we always have an array
  const selected = Array.isArray(selectedTagIds) ? selectedTagIds : [];

  // Function to handle selection changes
  const handleSelectionChange = (value) => {
    const tagId = parseInt(value, 10);
    let newSelection;

    if (selected.includes(tagId)) {
      // Remove tag if already selected
      newSelection = selected.filter(id => id !== tagId);
    } else {
      // Add tag if not selected
      newSelection = [...selected, tagId];
    }

    onChange(newSelection);
  };

  return (
    <div className="space-y-2">
      <Label>Tags</Label>
      {/* Flex container: the select is fixed at 300px and the selected tags appear to its right */}
      <div className="flex items-center gap-4">
        <Select value="" onValueChange={handleSelectionChange}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select tags">
              {selected.length ? `${selected.length} tags selected` : 'Select tags'}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {tags.map((tag) => (
              <SelectItem
                key={tag.id}
                value={tag.id.toString()}
                className="flex items-center justify-between py-2"
              >
                <span>{tag.name}</span>
                {selected.includes(tag.id) && (
                  <Check className="h-4 w-4 ml-2"/>
                )}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selected.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {selected.map(tagId => {
              const tag = tags.find(t => t.id === tagId);
              if (!tag) return null;
              return (
                <div
                  key={tagId}
                  className="inline-flex items-center px-3 py-2 text-sm rounded-full bg-primary/70 text-secondary-foreground"
                >
                  <span>{tag.name}</span>
                  <button
                    type="button"
                    className="ml-1 hover:text-primary"
                    onClick={() => handleSelectionChange(tagId.toString())}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

// Article editor dialog
export const ArticleEditor = ({
  article,
  isOpen,
  onClose,
  onSave,
  onApprove,
  onReject,
  onMakePending,
  onChangePublishState,
  tags = [],
}) => {
  const [formData, setFormData] = React.useState({
    title: '',
    content: '',
    excerpt: '',
    aiSummary: '',
    tagIds: [],
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
  const lastSavedDataRef = React.useRef({});

  React.useEffect(() => {
    if (article) {
      const data = {
        title: article.title || '',
        content: article.content || '',
        publishedAt: article.publishedAt || null,
        excerpt: article.excerpt || '',
        aiSummary: article.aiSummary || '',
        tagIds: article.tags?.map(tag => tag.id) || [],
      };
      setFormData(data);
      lastSavedDataRef.current = JSON.parse(JSON.stringify(data));
      setHasUnsavedChanges(false);
    }
  }, [article]);

  const handleSave = async () => {
    const dataToSave = {
      ...formData,
      tagIds: formData.tagIds || []
    };
    await onSave?.(dataToSave);
    lastSavedDataRef.current = formData;
    setHasUnsavedChanges(false);
  };

  const handleChange = (field, value) => {
    const newData = {
      ...formData,
      [field]: value,
    };
    setFormData(newData);
    setHasUnsavedChanges(JSON.stringify(newData) !== JSON.stringify(lastSavedDataRef.current));
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-[90vw] h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>
              Edit Article from Research "{article?.research?.suggestion?.title}"
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col gap-4 flex-1 overflow-auto px-4 py-2">
            {/* Basic fields */}
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  placeholder="Enter article title"
                />
              </div>
            </div>

            {/* Rich text editor */}
            <div className="space-y-2 flex-1">
              <Label>Content</Label>
              <RichTextEditor
                content={formData.content}
                onChange={(content) => handleChange('content', content)}
              />
            </div>

            {/* Metadata fields */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="excerpt">Excerpt</Label>
                <Textarea
                  id="excerpt"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.excerpt}
                  onChange={(e) => handleChange('excerpt', e.target.value)}
                  placeholder="Enter article excerpt"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="aiSummary">AI Summary</Label>
                <Textarea
                  id="aiSummary"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.aiSummary}
                  onChange={(e) => handleChange('aiSummary', e.target.value)}
                  placeholder="Enter AI summary"
                />
              </div>

              <TagsSelect
                tags={tags}
                selectedTagIds={formData.tagIds}
                onChange={(tagIds) => handleChange('tagIds', tagIds)}
              />
            </div>
          </div>

          <DialogFooter className="mt-4">
            <div className="flex justify-between w-full items-center"> {/* Added items-center */}
              <div className="space-x-2 flex items-center"> {/* Added flex and items-center */}
                <Button
                  variant="default"
                  onClick={handleSave}
                  disabled={!hasUnsavedChanges}
                >
                  Save Changes
                </Button>
                {hasUnsavedChanges && (
                  <span className="text-sm text-muted-foreground">
                    * You have unsaved changes
                  </span>
                )}
              </div>
              <div className="space-x-2 flex items-center"> {/* Added flex and items-center */}
                <Button variant="outline" onClick={onClose}>Close</Button>
                {article?.status !== 'APPROVED' && !article?.publishedAt && (
                  <Button
                    variant="default"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => onApprove?.(article.id)}
                    disabled={hasUnsavedChanges}
                  >
                    Approve
                  </Button>
                )}
                {article?.status !== 'REJECTED' && !article?.publishedAt && (
                  <Button
                    variant="destructive"
                    onClick={() => onReject?.(article.id)}
                    disabled={hasUnsavedChanges}
                  >
                    Reject
                  </Button>
                )}
                {(article?.status === 'APPROVED' || article?.status === 'REJECTED') && !article?.publishedAt && (
                  <Button
                    variant="secondary"
                    onClick={() => onMakePending?.(article.id)}
                    disabled={hasUnsavedChanges}
                    className="inline-flex items-center"
                  >
                    <History className="w-4 h-4 mr-2"/>
                    Make Pending
                  </Button>
                )}
                {article?.publishedAt && (
                  <Button
                    variant="destructive"
                    onClick={() => onChangePublishState?.(article.id, 'unpublish')}
                    disabled={hasUnsavedChanges}
                    className="inline-flex items-center"
                  >
                    Unpublish
                  </Button>
                )}
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};


