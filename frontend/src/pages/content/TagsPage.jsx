import React from 'react';
import { Plus } from 'lucide-react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { TagDialog, TagsTable } from '@/components/content/TagComponents';
import { contentService } from '@/services/content';

export const TagsPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [tags, setTags] = React.useState([]);
  const [editingTag, setEditingTag] = React.useState(null);
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch tags on mount and when status filter changes
  React.useEffect(() => {
    fetchTags();
  }, [statusFilter]);

  const fetchTags = async () => {
    try {
      setLoading(true);
      const data = await contentService.getTags(statusFilter === 'ALL' ? null : statusFilter);
      setTags(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load tags. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTag = async (tagData) => {
    try {
      if (tagData.id) {
        await contentService.updateTag(tagData.id, { name: tagData.name });
      } else {
        await contentService.createTag({ name: tagData.name });
      }
      toast({
        title: "Success",
        description: `Tag ${tagData.id ? 'updated' : 'created'} successfully`,
      });
      setEditingTag(null);
      fetchTags();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to ${tagData.id ? 'update' : 'create'} tag. Please try again.`,
      });
    }
  };

  const handleUpdateStatus = async (tag, newStatus) => {
    try {
      await contentService.updateTagStatus(tag.id, newStatus);
      toast({
        title: "Success",
        description: `Tag ${newStatus.toLowerCase()} successfully`,
      });
      fetchTags();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to update tag status. Please try again.`,
      });
    }
  };

  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  if (loading && !tags.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tag Management</h1>
        <Button onClick={() => setEditingTag({})}>
          <Plus className="h-4 w-4 mr-2" />
          Add Tag
        </Button>
      </div>

      <TagsTable
        data={tags}
        loading={loading}
        onEdit={setEditingTag}
        onApprove={(tag) => showConfirmDialog(
          "Approve Tag",
          "Are you sure you want to approve this tag?",
          () => handleUpdateStatus(tag, 'APPROVED')
        )}
        onReject={(tag) => showConfirmDialog(
          "Reject Tag",
          "Are you sure you want to reject this tag?",
          () => handleUpdateStatus(tag, 'REJECTED')
        )}
        onStatusFilterChange={setStatusFilter}
        currentStatusFilter={statusFilter}
        handleUpdateStatus={handleUpdateStatus}
      />

      <TagDialog
        tag={editingTag}
        isOpen={!!editingTag}
        onClose={() => setEditingTag(null)}
        onSave={handleSaveTag}
      />

      <AlertDialog
        open={confirmDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmDialog({
              open: false,
              title: '',
              description: '',
              action: null,
            });
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmDialog.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmDialog.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => {
              confirmDialog.action();
              setConfirmDialog({
                open: false,
                title: '',
                description: '',
                action: null,
              });
            }}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TagsPage;