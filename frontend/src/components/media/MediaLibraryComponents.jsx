import React from 'react';
import { X, Copy, ExternalLink } from 'lucide-react';
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";

// Media type badge
export const MediaTypeBadge = ({ type }) => {
  const styles = {
    IMAGE: 'bg-blue-100 text-blue-800',
    VIDEO: 'bg-purple-100 text-purple-800',
    DOCUMENT: 'bg-yellow-100 text-yellow-800',
    PDF: 'bg-red-100 text-red-800',
    SPREADSHEET: 'bg-green-100 text-green-800',
    OTHER: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[type] || styles.OTHER}`}>
      {type}
    </span>
  );
};

// Grid of media items
export const MediaGrid = ({ items, onSelect, selectedId }) => {
  if (!items?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No media items found.
      </div>
    );
  }

  return (
    <div className="media-grid">
      {items.map((item) => (
        <Card
          key={item.id}
          className={`cursor-pointer hover:border-primary transition-colors ${
            selectedId === item.id ? 'border-primary' : ''
          }`}
          onClick={() => onSelect(item)}
        >
          <div className="aspect-square relative">
            {item.mediaType === 'IMAGE' ? (
              <img
                src={`${import.meta.env.VITE_API_URL}${item.publicUrl}`}
                alt={item.title || item.originalFilename}
                className="absolute inset-0 w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-muted">
                <MediaTypeBadge type={item.mediaType}/>
              </div>
            )}
          </div>
          <CardContent className="p-2">
            <div className="truncate text-sm">
              {item.title || item.originalFilename}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Media details sidebar
export const MediaDetails = ({
 media,
 onClose,
 onUpdate,
 className = "",
}) => {
  const [formData, setFormData] = React.useState({
    title: '',
    caption: '',
    altText: '',
    instagramMediaType: '',
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);

  React.useEffect(() => {
    if (media) {
      setFormData({
        title: media.title || '',
        caption: media.caption || '',
        altText: media.altText || '',
        instagramMediaType: media.instagramMediaType || '',
      });
      setHasUnsavedChanges(false);
    }
  }, [media]);

  const handleChange = (field, value) => {
    setFormData(prev => {
      const newData = { ...prev, [field]: value || null };
      setHasUnsavedChanges(true);
      return newData;
    });
  };

  const handleSave = async () => {
    const metadata = {
      title: formData.title || null,
      caption: formData.caption || null,
      altText: formData.altText || null,
      instagramMediaType: formData.instagramMediaType || null
    };
  
    // Remove null values
    Object.keys(metadata).forEach(key =>
      metadata[key] === null && delete metadata[key]
    );

    await onUpdate?.(media.id, metadata);
    setHasUnsavedChanges(false);
  };

  if (!media) return null;

  return (
    <Card className="h-[calc(100vh_+_10px)] border-0">
      <CardHeader className="sticky top-0 z-10 bg-background px-4 py-3 -my-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium">Media Details</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="px-4">
        <div className="space-y-6">
          {media.mediaType === 'IMAGE' && (
            <div className="relative aspect-video">
              <img
                src={`${import.meta.env.VITE_API_URL}${media.publicUrl}`}
                alt={media.title || media.originalFilename}
                className="absolute inset-0 w-full h-full object-contain"
              />
            </div>
          )}

          {/* Form fields */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                placeholder="Enter media title"
                className="w-full"
              />
            </div>

            <div>
              <Label htmlFor="caption">Caption</Label>
              <Textarea
                id="caption"
                value={formData.caption}
                onChange={(e) => handleChange('caption', e.target.value)}
                placeholder="Enter caption"
                className="w-full"
              />
            </div>

            <div>
              <Label htmlFor="altText">Alt Text</Label>
              <Input
                id="altText"
                value={formData.altText}
                onChange={(e) => handleChange('altText', e.target.value)}
                placeholder="Enter alt text"
                className="w-full"
              />
            </div>

            {media.mediaType === 'IMAGE' && (
              <div>
                <Label htmlFor="instagramMediaType">Instagram Media Type</Label>
                <Select
                  value={formData.instagramMediaType}
                  onValueChange={(value) => handleChange('instagramMediaType', value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select media type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SQUARE">Square (1:1)</SelectItem>
                    <SelectItem value="PORTRAIT">Portrait (4:5)</SelectItem>
                    <SelectItem value="LANDSCAPE">Landscape (1.91:1)</SelectItem>
                    <SelectItem value="STORY">Story (9:16)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* File Info */}
            <div className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Type</Label>
                  <div className="text-sm mt-1">
                    <MediaTypeBadge type={media.mediaType} />
                  </div>
                </div>
                <div>
                  <Label>Size</Label>
                  <div className="text-sm mt-1">
                    {Math.round(media.fileSize / 1024)} KB
                  </div>
                </div>
              </div>

              {media.width && media.height && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Dimensions</Label>
                    <div className="text-sm mt-1">
                      {media.width} × {media.height}
                    </div>
                  </div>
                  <div>
                    <Label>Aspect Ratio</Label>
                    <div className="text-sm mt-1">
                      {(media.width / media.height).toFixed(2)}:1
                    </div>
                  </div>
                </div>
              )}

              <div>
                <Label>Original Filename</Label>
                <div className="text-sm mt-1">{media.originalFilename}</div>
              </div>

              {media.source === 'WIKIMEDIA' && media.attribution && (
                <div>
                  <Label>Attribution</Label>
                  <div className="text-sm mt-1 space-y-1">
                    <div>{media.attribution}</div>
                    {media.licenseUrl && (
                      <a
                        href={media.licenseUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline inline-flex items-center"
                      >
                        License details
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    )}
                  </div>
                </div>
              )}

              {media.source === 'WIKIMEDIA' && media.commonsId && (
                <div>
                  <Label>Wikimedia Commons</Label>
                  <div className="text-sm mt-1">
                    <a
                      href={`https://commons.wikimedia.org/wiki/${encodeURIComponent(media.commonsId)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center"
                    >
                      View on Commons
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  </div>
                </div>
              )}

              {/* Path */}
              <div>
                <Label>File Path</Label>
                <div className="flex items-center gap-2 mt-1">
                  <code className="text-xs bg-muted p-1 rounded flex-1 overflow-x-auto">
                    {media.filePath}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigator.clipboard.writeText(media.filePath)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
      {hasUnsavedChanges && (
        <div className="sticky bottom-0 border-t bg-background p-4">
          <Button className="w-full" onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      )}
    </Card>
  );
};