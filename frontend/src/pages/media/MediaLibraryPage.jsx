import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { MediaGrid, MediaDetails } from '@/components/media/MediaLibraryComponents';
import { MediaUpload } from '@/components/media/MediaUpload';
import { contentService } from '@/services/content';

export const MediaLibraryPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [mediaItems, setMediaItems] = React.useState([]);
  const [selectedMedia, setSelectedMedia] = React.useState(null);
  const [typeFilter, setTypeFilter] = React.useState('ALL');

  // Fetch media items on mount and when type filter changes
  React.useEffect(() => {
    fetchMediaItems();
  }, [typeFilter]);

  const fetchMediaItems = async () => {
    try {
      setLoading(true);
      const data = await contentService.getMediaLibrary(
        typeFilter === 'ALL' ? null : typeFilter
      );
      setMediaItems(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load media library. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    try {
      await contentService.uploadMedia(file);
      toast({
        title: "Success",
        description: "Media uploaded successfully",
      });
      fetchMediaItems();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to upload media. Please try again.",
      });
      throw error; // Re-throw to be handled by upload component
    }
  };

  const handleUpdateMetadata = async (id, metadata) => {
    try {
      await contentService.updateMediaMetadata(id, metadata);
      toast({
        title: "Success",
        description: "Media details updated successfully",
      });
      // Update the selected media with new metadata
      setSelectedMedia(prev => ({
        ...prev,
        ...metadata,
      }));
      // Update the item in the grid
      setMediaItems(prev =>
        prev.map(item =>
          item.id === id
            ? { ...item, ...metadata }
            : item
        )
      );
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update media details. Please try again.",
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Media Library</h1>

        <div className="flex items-center space-x-2">
          <Label>Type:</Label>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All types</SelectItem>
              <SelectItem value="IMAGE">Images</SelectItem>
              <SelectItem value="VIDEO">Videos</SelectItem>
              <SelectItem value="DOCUMENT">Documents</SelectItem>
              <SelectItem value="PDF">PDFs</SelectItem>
              <SelectItem value="SPREADSHEET">Spreadsheets</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <MediaUpload onUpload={handleUpload} className="mb-4" />

      <div className="flex gap-4">
        {/* Main content area */}
        <div className={`flex-1 transition-all ${selectedMedia ? 'pr-80' : ''}`}>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <MediaGrid
              items={mediaItems}
              selectedId={selectedMedia?.id}
              onSelect={setSelectedMedia}
            />
          )}
        </div>

        {/* Details sidebar */}
        {selectedMedia && (
          <div className="fixed top-0 right-0 w-80 h-screen bg-background border-l p-4 overflow-y-auto">
            <MediaDetails
              media={selectedMedia}
              onClose={() => setSelectedMedia(null)}
              onUpdate={handleUpdateMetadata}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default MediaLibraryPage;