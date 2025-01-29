import React from 'react';
import { Check, MoreHorizontal, X, Share2, MessageCircle, History } from 'lucide-react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button } from '@/components/ui/button';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import RichTextEditor from '@/components/ui/RichTextEditor';

// Status badge component
export const ArticleStatus = ({ status }) => {
  switch (status) {
    case 'APPROVED':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <Check className="w-4 h-4 mr-1" />
          Approved
        </span>
      );
    case 'REJECTED':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <X className="w-4 h-4 mr-1" />
          Rejected
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <span className="w-2 h-2 mr-1 rounded-full bg-yellow-400" />
          Pending
        </span>
      );
  }
};

// Did You Know generator dialog
const GenerateDYKDialog = ({
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

const TagsSelect = ({ tags, selectedTagIds = [], onChange }) => {
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
      <Select
        value=""
        onValueChange={handleSelectionChange}
      >
        <SelectTrigger className="w-full">
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
                className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-secondary text-secondary-foreground"
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

          <div className="flex flex-col gap-4 flex-1 overflow-auto">
            {/* Basic fields */}
            <div className="grid grid-cols-2 gap-4">
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
                <Input
                  id="excerpt"
                  value={formData.excerpt}
                  onChange={(e) => handleChange('excerpt', e.target.value)}
                  placeholder="Enter article excerpt"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="aiSummary">AI Summary</Label>
                <Input
                  id="aiSummary"
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
                {article?.status !== 'APPROVED' && (
                  <Button
                    variant="default"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => onApprove?.(article.id)}
                    disabled={hasUnsavedChanges}
                  >
                    Approve
                  </Button>
                )}
                {article?.status !== 'REJECTED' && (
                  <Button
                    variant="destructive"
                    onClick={() => onReject?.(article.id)}
                    disabled={hasUnsavedChanges}
                  >
                    Reject
                  </Button>
                )}
                {(article?.status === 'APPROVED' || article?.status === 'REJECTED') && (
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
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

// Articles table
export const ArticlesTable = ({
    data,
    loading,
    onEdit,
    onApprove,
    onReject,
    onMakePending,
    onGenerateStory,
    onGenerateDidYouKnow,
    onStatusFilterChange,
    currentStatusFilter,
  }) => {
  const [dykDialogOpen, setDykDialogOpen] = React.useState(false);
  const [selectedArticleId, setSelectedArticleId] = React.useState(null);

  const handleGenerateDYK = async (count) => {
    await onGenerateDidYouKnow?.(selectedArticleId, count);
    setDykDialogOpen(false);
  };

  const columns = [
    {
      accessorKey: "title",
      header: "Title",
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({row}) => <ArticleStatus status={row.getValue("status")}/>,
    },
    {
      accessorKey: "tags",
      header: "Tags",
      cell: ({row}) => {
        const tags = row.getValue("tags") || [];
        return (
          <div className="flex flex-wrap gap-1">
            {tags.map(tag => (
              <span key={tag.id} className="px-2 py-1 text-xs rounded-full bg-secondary text-secondary-foreground">
                {tag.name}
              </span>
            ))}
          </div>
        );
      }
    },
    {
      id: "actions",
      cell: ({row}) => {
        const article = row.original;
        const status = article.status;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4"/>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit?.(article)}>
                Review Article
              </DropdownMenuItem>
              {status !== 'APPROVED' && (
                <DropdownMenuItem
                  className="text-green-600"
                  onClick={() => onApprove?.(article.id)}
                >
                  Approve
                </DropdownMenuItem>
              )}
              {status !== 'REJECTED' && (
                <DropdownMenuItem
                  className="text-red-600"
                  onClick={() => onReject?.(article.id)}
                >
                  Reject
                </DropdownMenuItem>
              )}
              {(status === 'APPROVED' || status === 'REJECTED') && (
                <DropdownMenuItem
                  onClick={() => onMakePending?.(article.id)}
                >
                  Make Pending
                </DropdownMenuItem>
              )}
              {status === 'APPROVED' && (
                <>
                  <hr></hr>
                  <DropdownMenuItem onClick={() => onGenerateStory?.(article.id)}>
                    <Share2 className="h-4 w-4 mr-2" />
                    Generate Story
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      setSelectedArticleId(article.id);
                      setDykDialogOpen(true);
                    }}
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Generate DYK Posts
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    }
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Label>Status Filter:</Label>
        <Select value={currentStatusFilter || ''} onValueChange={onStatusFilterChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Table>
          <TableHeader className="sticky top-0 bg-white z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No articles found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <GenerateDYKDialog
        isOpen={dykDialogOpen}
        onClose={() => {
          setDykDialogOpen(false);
          setSelectedArticleId(null);
        }}
        onGenerate={handleGenerateDYK}
      />
    </div>
  );
};

