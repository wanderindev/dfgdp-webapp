import React from 'react';
import {Plus} from 'lucide-react';
import {useToast} from "@/components/ui/use-toast";
import {Button} from '@/components/ui/button';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  GenerateSuggestionsDialog,
  SuggestionDialog,
  SuggestionsTable
} from '@/components/content/SuggestionComponents';
import {contentService} from '@/services/content';

export const SuggestionsPage = () => {
  const {toast} = useToast();
  const [loading, setLoading] = React.useState(true);
  const [suggestions, setSuggestions] = React.useState([]);
  const [taxonomies, setTaxonomies] = React.useState([]);
  const [editingSuggestion, setEditingSuggestion] = React.useState(null);
  const [generatingSuggestions, setGeneratingSuggestions] = React.useState(false);
  const [generationInProgress, setGenerationInProgress] = React.useState(false);
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch suggestions and taxonomies on mount and when status filter changes
  React.useEffect(() => {
    fetchSuggestions();
    fetchTaxonomies();
  }, [statusFilter]);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const data = await contentService.getSuggestions(
        statusFilter === 'ALL' ? null : statusFilter
      );
      setSuggestions(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load suggestions. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTaxonomies = async () => {
    try {
      const data = await contentService.getTaxonomies();
      setTaxonomies(data || []);
    } catch (error) {
      console.error('Error fetching taxonomies:', error);
    }
  };

  const handleGenerateSuggestions = async (data) => {
    try {
      // Convert string values to integers
      const mutationData = {
        categoryId: parseInt(data.categoryId, 10),
        count: parseInt(data.count, 10)
      };

      await contentService.generateSuggestions(mutationData);
      setGeneratingSuggestions(false);
      setGenerationInProgress(true);
      toast({
        title: "Success",
        description: "Suggestions generation started. They will be available in a few minutes.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to generate suggestions. Please try again.",
      });
    }
  };

  const handleUpdateSuggestion = async (suggestionData) => {
    try {
      await contentService.updateSuggestion(suggestionData.id, suggestionData);
      toast({
        title: "Success",
        description: "Suggestion updated successfully",
      });
      setEditingSuggestion(null);
      fetchSuggestions();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update suggestion. Please try again.",
      });
    }
  };

  const handleUpdateStatus = async (suggestion, newStatus) => {
    try {
      await contentService.updateSuggestionStatus(suggestion.id, newStatus);
      toast({
        title: "Success",
        description: `Suggestion ${newStatus.toLowerCase()} successfully`,
      });
      fetchSuggestions();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update suggestion status. Please try again.",
      });
    }
  };

  const handleGenerateResearch = async (suggestion) => {
    try {
      await contentService.generateResearch(suggestion.id);
      toast({
        title: "Success",
        description: "Research generation started. It will be available in a few minutes.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to start research generation. Please try again.",
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

  if (loading && !suggestions.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Article Suggestions</h1>
        <Button onClick={() => setGeneratingSuggestions(true)}>
          <Plus className="h-4 w-4 mr-2"/>
          Generate Suggestions
        </Button>
      </div>

      <SuggestionsTable
        data={suggestions}
        loading={loading}
        onEdit={setEditingSuggestion}
        onGenerateResearch={(suggestion) => showConfirmDialog(
          "Generate Research",
          `Are you sure you want to generate research for "${suggestion.title}"?`,
          () => handleGenerateResearch(suggestion)
        )}
        onUpdateStatus={(suggestion, status) => showConfirmDialog(
          `${status.charAt(0) + status.slice(1).toLowerCase()} Suggestion`,
          `Are you sure you want to mark this suggestion as ${status.toLowerCase()}?`,
          () => handleUpdateStatus(suggestion, status)
        )}
        onStatusFilterChange={setStatusFilter}
        currentStatusFilter={statusFilter}
      />

      <GenerateSuggestionsDialog
        isOpen={generatingSuggestions}
        onClose={() => setGeneratingSuggestions(false)}
        onGenerate={handleGenerateSuggestions}
        taxonomies={taxonomies}
      />

      <SuggestionDialog
        suggestion={editingSuggestion}
        isOpen={!!editingSuggestion}
        onClose={() => setEditingSuggestion(null)}
        onSave={handleUpdateSuggestion}
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

      <Dialog
        open={generationInProgress}
        onOpenChange={() => setGenerationInProgress(false)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generating Suggestions</DialogTitle>
          </DialogHeader>
          <p>
            Your suggestions are being generated and will be available in a few minutes.
            You can close this dialog and continue working.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SuggestionsPage;