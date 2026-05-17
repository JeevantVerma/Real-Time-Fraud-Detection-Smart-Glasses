const MetricRow = ({ label, value, emphasize = false, loading = false }) => {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      <span
        className={`font-mono ${
          emphasize ? "text-white" : "text-slate-200"
        } ${loading ? "animate-pulse" : ""}`}
      >
        {value}
      </span>
    </div>
  );
};

export default MetricRow;
