import { useEffect, useRef, useState } from 'react';
import styles from './dropdown.module.css'; // Import the CSS module
import { FiChevronDown, FiX } from 'react-icons/fi';

const DynamicDropdown = ({ options, multiple = false, onChange, label, selectedItems }) => {
  const [search, setSearch] = useState('');
  const [openDropdown, setOpenDropdown] = useState(false);

  const wrapperRef = useRef(null);

  const filteredOptions = options.filter(
    (opt) =>
      opt.label.toLowerCase().includes(search.toLowerCase()) ||
      opt.category.toLowerCase().includes(search.toLowerCase())
  );

  const toggleMulti = (opt) => {
    const exists = selectedItems.find((item) => item.label === opt.label);
    const updatedSelection = exists
      ? selectedItems.filter((item) => item.label !== opt.label)
      : [...selectedItems, opt];
    onChange(updatedSelection);
  };

  const selectSingle = (opt) => {
    onChange([opt]);
    setOpenDropdown(false);
    setSearch('');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpenDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={styles.ddDropdownWrapper} ref={wrapperRef}>
      <div className={styles.ddDropdown}>
        <button
          className={styles.ddDropdownButton}
          onClick={() => setOpenDropdown((prevState) => !prevState)}
        >
          {multiple
            ? `${selectedItems.length} Selected`
            : selectedItems[0]?.label || `Select ${label}`}
          <span className={`${styles.ddDropdownArrow} ${openDropdown ? styles.open : ''}`}>
            <FiChevronDown />
          </span>
        </button>

        {openDropdown && (
          <div className={styles.ddDropdownMenu}>
            <input
              className={styles.ddSearchInput}
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <ul className={styles.ddDropdownList}>
              {filteredOptions.length === 0 && (
                <li className={styles.ddEmptyState}>No options found.</li>
              )}
              {filteredOptions.map((opt) => (
                <li
                  key={opt.label}
                  className={`${styles.ddDropdownItem} ${
                    selectedItems.some((item) => item.label === opt.label) ? styles.selected : ''
                  }`}
                  onClick={() => (multiple ? toggleMulti(opt) : selectSingle(opt))}
                >
                  {opt.label}
                  <span className={styles.ddCategory}>({opt.category})</span>
                  {multiple && selectedItems.some((item) => item.label === opt.label) && (
                    <span className="checkmark">✓</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {multiple && selectedItems.length > 0 && (
        <div className={styles.ddTagsContainer}>
          {selectedItems.map((item) => (
            <span key={item.label} className={styles.ddTag}>
              {item.label}
              <button
                className={styles.ddTagRemove}
                onClick={() => toggleMulti(item)}
              >
                <FiX />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default DynamicDropdown;
