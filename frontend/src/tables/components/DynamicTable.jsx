// style
import general from "../../style/general.module.css";

// components
import { SearchBar } from "../../components/component/General";
import Pagination from "../../components/component/Pagination";

// react
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { format } from "date-fns";

function TableHeader({ headers }) {
  return (
    <tr className={general.header}>
      {headers.map((header) => (
        <th key={header}>{header}</th>
      ))}
    </tr>
  );
}

function TableItem({ item, columns }) {
  const navigate = useNavigate();
  return (
    <tr className={general.item}>
      {columns.map((col) => (
        <td key={col.key}>
          {col.format ? col.format(item[col.key]) : item[col.key]}
        </td>
      ))}
      {/* Add a dynamic button if "action" column is passed */}
      {columns.some((col) => col.key === "action") && (
        <td>
          <button
            className={general.btn}
            onClick={() => navigate(`/admin/archive/${item.id}`)} // Assuming 'id' is the unique identifier
          >
            👁
          </button>
        </td>
      )}
    </tr>
  );
}

export default function DynamicTable({
  data = [],
  headers = [], // Column headers passed dynamically
  columns = [], // Column definitions with keys to access values dynamically
  searchValue = "",
  onSearchChange,
  activeTab,
}) {
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedData = data.slice(startIndex, endIndex);

  return (
    <div className={general.ticketTableSection}>
      <div className={general.tableHeader}>
        {/* <h2>
          {activeTab} ({data.length})
        </h2>
        <div className={general.tableActions}>
          <SearchBar value={searchValue} onChange={onSearchChange} />
          <button className={general.exportButton}>Export</button>
        </div> */}
      </div>
      <div className={general.ticketTableWrapper}>
        <table className={general.ticketTable}>
          <thead>
            <TableHeader headers={headers} />
          </thead>
          <tbody>
            {data.length > 0 ? (
              paginatedData.map((item) => (
                <TableItem key={item.id} item={item} columns={columns} />
              ))
            ) : (
              <tr>
                <td colSpan={headers.length} className={general.noData}>
                  No data found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className={general.ttPagination}>
        <Pagination
          currentPage={currentPage}
          pageSize={pageSize}
          totalItems={data.length}
          onPageChange={setCurrentPage}
          onPageSizeChange={setPageSize}
        />
      </div>
    </div>
  );
}
