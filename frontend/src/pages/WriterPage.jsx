import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import DataTable from '@/components/shared/DataTable';
import ContentStatus from '@/components/shared/ContentStatus';
import StepStatus from '@/components/shared/StepStatus';
import ConfirmationDialog from '@/components/shared/ConfirmationDialog';
import GenerationDialog from '@/components/shared/GenerationDialog';
import { contentService } from '@/services/content';
import { ArticleEditor, GenerateDYKDialog } from '@/components/WriterComponents.jsx';
import { ArrowUpDown } from 'lucide-react';

export const WriterPage = () => {
  const { toast } = useToast();

  // Data state
  const [articles, setArticles] = React.useState([]);
  const [tags, setTags] = React.useState([]);

  // UI state
  const [loading, setLoading] = React.useState(true);
  const [editingArticle, setEditingArticle] = React.useState(null);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });
  const [selectedArticleId, setSelectedArticleId] = React.useState(null);
  const [dykDialogOpen, setDykDialogOpen] = React.useState(false);

  // Filtering, Sorting & Pagination state
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [sorting, setSorting] = React.useState([]); // e.g. [{ id: 'title', desc: false }]
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 12;

  // Fetch articles with pagination, sorting, filtering
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const sortParam = sorting[0]?.id || 'title';
      const direction = sorting[0]?.desc ? 'desc' : 'asc';

      const data = await contentService.getArticles(
        currentPage,
        pageSize,
        statusFilter === 'ALL' ? null : statusFilter,
        globalFilter,
        sortParam,
        direction
      );

      // noinspection JSUnresolvedReference
      setArticles(data.articles || []);
      setTotalPages(data.pages || 1);
    } catch (error) {
      console.error("Error fetching articles:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load articles. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch tags for article metadata (only approved tags)
  const fetchTags = async () => {
    try {
      const data = await contentService.getAllTags('APPROVED');
      setTags(data || []);
    } catch (error) {
      console.error("Error fetching tags:", error);
    }
  };

  // Re-fetch articles whenever any filter/sort/pagination state changes
  React.useEffect(() => {
    (async () => {
      await fetchArticles();
    })();
  }, [globalFilter, statusFilter, sorting, currentPage]);

  // Fetch tags on mount
  React.useEffect(() => {
    (async () => {
      await fetchTags();
    })();
  }, []);

  // Handler for updating (saving) an article from the editor
  const handleUpdateArticle = async (articleData, fromActions) => {
    try {
      const updatedArticle = await contentService.updateArticle(editingArticle.id, articleData);
      toast({
        title: "Success",
        description: "Article updated successfully",
      });
      // Update the modal data with the updated article instead of closing it.
      if (!fromActions) setEditingArticle(updatedArticle);
      await fetchArticles();
    } catch (error) {
      console.log("Error updating article:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update article. Please try again.",
      });
    }
  };

  // Handler for updating article status
  const handleUpdateStatus = async (articleId, status, fromActions) => {
    try {
      const updatedArticle = await contentService.updateArticleStatus(articleId, status);
      toast({
        title: "Success",
        description: `Article ${status.toLowerCase()} successfully`,
      });
      // Update editingArticle so the modal remains open with new data.
      if (!fromActions) setEditingArticle(updatedArticle);
      await fetchArticles();
    } catch (error) {
      console.log("Error updating article status:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to update article status. Please try again.`,
      });
    }
  };

  const handlePublishState = async (articleId, state, fromActions) => {
    try {
      const updatedArticle = await contentService.updateArticlePublishState(articleId, state);
      toast({
        title: "Success",
        description: `Article ${state === "publish" ? "published" : "unpublished"} successfully.`,
      });
      // Update editingArticle to reflect the new published_at value.
      if (!fromActions) setEditingArticle(updatedArticle);
      await fetchArticles();
    } catch (error) {
      console.error("Error updating publish state:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update publish state. Please try again.",
      });
    }
  };

  // Handler for generating a story promotion
  const handleGenerateStory = async (articleId) => {
    try {
      const { success, message } = await contentService.generateStoryPromotion(articleId);
      setGenerationInProgress(true);
      if (!success) {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
    } catch (error) {
      console.log("Error generating story promotion:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start story generation. Please try again.",
      });
    }
  };

  // Handler for generating DYK posts
  const handleGenerateDidYouKnow = async (articleId, count) => {
    try {
      const { success, message } = await contentService.generateDidYouKnowPosts(articleId, count);
      setGenerationInProgress(true);
      if (!success) {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
    } catch (error) {
      console.log("Error generating DYK posts:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start posts generation. Please try again.",
      });
    }
  };

  // Helper to show the confirmation dialog
  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  // Define the row-level actions for articles
  // noinspection JSUnresolvedReference
  const articleActions = [
    {
      label: "Review Article",
      onClick: (article) => setEditingArticle(article),
      shouldShow: () => true,
    },
    {
      label: "Approve",
      onClick: (article) =>
        showConfirmDialog(
          "Approve Article",
          "Are you sure you want to approve this article?",
          () => handleUpdateStatus(article.id, 'APPROVED', true)
        ),
      shouldShow: (article) => article.status !== 'APPROVED',
    },
    {
      label: "Reject",
      onClick: (article) =>
        showConfirmDialog(
          "Reject Article",
          "Are you sure you want to reject this article?",
          () => handleUpdateStatus(article.id, 'REJECTED', true)
        ),
      // Show Reject if the article is not rejected and not published.
      shouldShow: (article) => article.status !== 'REJECTED' && !article.publishedAt,
    },
    {
      label: "Make Pending",
      onClick: (article) =>
        showConfirmDialog(
          "Make Pending",
          "Are you sure you want to set this article back to pending status?",
          () => handleUpdateStatus(article.id, 'PENDING', true)
        ),
      shouldShow: (article) => article.status !== 'PENDING' && !article.publishedAt,
    },
    {
      label: "Publish",
      onClick: (article) =>
        showConfirmDialog(
          "Publish Article",
          "Are you sure you want to publish this article?",
          () => handlePublishState(article.id, "publish", true)
        ),
      // Show Publish if the article is approved and not yet published.
      shouldShow: (article) => article.status === 'APPROVED' && !article.publishedAt,
    },
    {
      label: "Unpublish",
      onClick: (article) =>
        showConfirmDialog(
          "Unpublish Article",
          "Are you sure you want to unpublish this article?",
          () => handlePublishState(article.id, "unpublish", true)
        ),
      // Show Unpublish if the article is published.
      shouldShow: (article) => Boolean(article.publishedAt),
    },
    {
      label: "Generate Story",
      onClick: (article) =>
        showConfirmDialog(
          "Generate Story",
          "Are you sure you want to generate a story promotion for this article?",
          () => handleGenerateStory(article.id)
        ),
      shouldShow: (article) => false, //article.status === 'APPROVED',
    },
    {
      label: "Generate DYK Posts",
      onClick: (article) => {
        setSelectedArticleId(article.id);
        setDykDialogOpen(true);
      },
      shouldShow: (article) => false // article.status === 'APPROVED',
    },
  ];

  // Configure columns for DataTable.
  const columnsOrder = ['title', 'status', 'tagsAdded', 'published'];
  const columnsOverride = [
    {
      accessorKey: 'title',
      header: 'Title',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <ContentStatus status={row.getValue('status')} />,
    },
    {
      id: 'tagsAdded',
      accessorKey: 'tagsAdded',
      header: () => (
        <Button
          variant="ghost"
          className="hover:bg-transparent focus:bg-transparent px-0"
          onClick={() =>
            setSorting((prev) => {
              const existingSort = prev.find((s) => s.id === 'tagsAdded');
              if (!existingSort) {
                return [{ id: 'tagsAdded', desc: false }];
              }
              return [{ id: 'tagsAdded', desc: !existingSort.desc }];
            })
          }
        >
          Tags Added
          <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
        </Button>
      ),
      cell: ({ row }) => {
        const done = row.original.tags && row.original.tags.length > 0;
        return <StepStatus done={done} />;
      },
    },
    {
      id: 'published',
      accessorKey: 'published',
      header: () => (
        <Button
          variant="ghost"
          className="hover:bg-transparent focus:bg-transparent px-0"
          onClick={() =>
            setSorting((prev) => {
              const existingSort = prev.find((s) => s.id === 'published');
              if (!existingSort) {
                return [{ id: 'published', desc: false }];
              }
              return [{ id: 'published', desc: !existingSort.desc }];
            })
          }
        >
          Published
          <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
        </Button>
      ),
      cell: ({ row }) => {
        // Mark as done if published_at is not null.
        // noinspection JSUnresolvedReference
        const done = row.original.publishedAt !== null;
        return <StepStatus done={done} />;
      },
    },
  ];
  const columnWidths = {
    status: 'w-[250px]',
    tagsAdded: 'w-[250px]',
    published: 'w-[250px]',
    actions: 'w-[100px]',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Writer Dashboard</h1>
      </div>

      <DataTable
        data={articles}
        loading={loading}
        actions={articleActions}
        // Server‑side pagination & sorting
        pageCount={totalPages}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        sorting={sorting}
        setSorting={setSorting}
        globalFilter={globalFilter}
        setGlobalFilter={setGlobalFilter}
        // Filters
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        showStatusFilter={true}
        // Column configuration
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        pageSize={pageSize}
      />

      {editingArticle && (
        <ArticleEditor
          article={editingArticle}
          isOpen={!!editingArticle}
          onClose={() => setEditingArticle(null)}
          onSave={handleUpdateArticle}
          onApprove={(id) => handleUpdateStatus(id, 'APPROVED')}
          onReject={(id) => handleUpdateStatus(id, 'REJECTED')}
          onMakePending={(id) =>
            showConfirmDialog(
              "Make Pending",
              "Are you sure you want to set this article back to pending status?",
              () => handleUpdateStatus(id, 'PENDING')
            )
          }
          onGenerateStory={handleGenerateStory}
          onGenerateDidYouKnow={handleGenerateDidYouKnow}
          onChangePublishState={handlePublishState}
          tags={tags}
        />
      )}

      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        description={confirmDialog.description}
        onConfirm={() => {
          confirmDialog.action?.();
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          });
        }}
        onClose={() =>
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          })
        }
      />

      <GenerationDialog
        open={generationInProgress}
        onOpenChange={(open) => {
          if (!open) setGenerationInProgress(false);
        }}
        resource="Content"
      />

      <GenerateDYKDialog
        isOpen={dykDialogOpen}
        onClose={() => {
          setDykDialogOpen(false);
          setSelectedArticleId(null);
        }}
        onGenerate={handleGenerateDidYouKnow}
      />
    </div>
  );
};
