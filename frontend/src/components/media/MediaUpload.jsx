import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

export const MediaUpload = ({
  onUpload,
  multiple = true,
  children,
  className = "",
}) => {
  const [uploadProgress, setUploadProgress] = React.useState({});
  const [isUploading, setIsUploading] = React.useState(false);

  const onDrop = React.useCallback(async (acceptedFiles) => {
    setIsUploading(true);
    const newProgress = {};

    try {
      for (const file of acceptedFiles) {
        newProgress[file.name] = 0;
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));

        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            const currentProgress = prev[file.name] || 0;
            if (currentProgress >= 90) {
              clearInterval(progressInterval);
              return prev;
            }
            return {
              ...prev,
              [file.name]: currentProgress + 10,
            };
          });
        }, 500);

        // Upload file
        await onUpload(file);

        // Complete progress
        clearInterval(progressInterval);
        setUploadProgress(prev => ({ ...prev, [file.name]: 100 }));
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
      // Clear progress after a delay
      setTimeout(() => {
        setUploadProgress({});
      }, 1000);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.svg'],
    },
    multiple,
  });

  return (
    <>
      <div
        {...getRootProps()}
        className={`
          ${className}
          cursor-pointer
          ${isDragActive ? 'border-primary' : 'border-dashed'}
          border-2 rounded-lg p-4
          transition-colors duration-200
          hover:border-primary
          focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
        `}
      >
        <input {...getInputProps()} />
        {children || (
          <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <Upload className="h-8 w-8" />
            <p>Drag & drop media here, or click to select</p>
          </div>
        )}
      </div>

      <Dialog open={isUploading}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Uploading Media</DialogTitle>
            <DialogDescription>
              Please wait while your files are being uploaded...
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="truncate">{filename}</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};