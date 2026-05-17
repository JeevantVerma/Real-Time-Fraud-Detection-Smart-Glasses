const UploadCard = ({
  title,
  description,
  accept,
  file,
  onFileChange,
  withPanel = true,
}) => {
  const content = (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-lg font-display font-semibold">{title}</h3>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
      <label className="flex flex-col gap-2 text-sm">
        <span className="text-slate-300">Upload file</span>
        <input
          type="file"
          accept={accept}
          onChange={(event) => onFileChange(event.target.files[0])}
          className="w-full rounded-lg border border-slate-700 bg-inkSoft px-3 py-2 text-sm text-slate-200 file:mr-3 file:rounded-md file:border-0 file:bg-slate-800 file:px-3 file:py-1 file:text-xs file:text-slate-200"
        />
      </label>
      <div className="text-xs text-slate-400">
        {file ? `Selected: ${file.name}` : "No file selected"}
      </div>
    </div>
  );

  if (!withPanel) {
    return content;
  }

  return <div className="glass-panel rounded-2xl p-6">{content}</div>;
};

export default UploadCard;
