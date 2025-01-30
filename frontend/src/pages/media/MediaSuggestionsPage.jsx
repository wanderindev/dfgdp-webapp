import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import { MediaSuggestionsTable } from '@/components/media/MediaSuggestionsComponents';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { contentService } from '@/services/content';

export const MediaSuggestionsPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [suggestions, setSuggestions] = React.useState([]);
  const [fetchInProgress, setFetchInProgress] = React.useState(false);

  // Fetch suggestions on mount
  React.useEffect(() => {
    (async () => {
      try {
        await fetchSuggestions()
      } catch (error) {
        console.error("Something went wrong:", error);
      }
    })();
  }, []);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const data = await contentService.getMediaSuggestions();
      setSuggestions(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load media suggestions. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFetchCandidates = async (suggestionId) => {
    try {
      const { success, message } = await contentService.fetchCandidates(suggestionId);

      setFetchInProgress(true);

      if (success) {
        toast({
          title: "Success",
          description: message,
        });
      } else {
        toast({
          variant: "destructive",
          title: "Error",
          description: message,
        });
      }
      // Refresh data to show updated counts
      fetchSuggestions();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to fetch candidates. Please try again.",
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Media Suggestions</h1>
      </div>

      <MediaSuggestionsTable
        data={suggestions}
        loading={loading}
        onFetchCandidates={handleFetchCandidates}
      />

      <Dialog
        open={fetchInProgress}
        onOpenChange={() => setFetchInProgress(false)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Fetching Candidates</DialogTitle>
          </DialogHeader>
          <p>
            Candidates are being fetched from Wikimedia Commons and will be available in a few minutes.
            You can close this dialog and continue working.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
};