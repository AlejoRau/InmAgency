// ===== COPY TO CLIPBOARD =====
function copyToClipboard(elementId, btn) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const text = el.innerText || el.textContent;

  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = '¡Copiado!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    // Fallback for older browsers
    const range = document.createRange();
    range.selectNode(el);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    document.execCommand('copy');
    window.getSelection().removeAllRanges();
    btn.textContent = '¡Copiado!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copiar';
      btn.classList.remove('copied');
    }, 2000);
  });
}

// ===== PHOTO PREVIEW =====
const fotoInput = document.getElementById('fotos');
const photoPreview = document.getElementById('photoPreview');

if (fotoInput && photoPreview) {
  fotoInput.addEventListener('change', () => {
    photoPreview.innerHTML = '';
    const files = Array.from(fotoInput.files);

    files.forEach((file, index) => {
      if (!file.type.startsWith('image/')) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const wrap = document.createElement('div');
        wrap.className = 'preview-wrap';

        const img = document.createElement('img');
        img.src = e.target.result;
        img.className = 'preview-img';
        img.alt = file.name;

        wrap.appendChild(img);

        if (index === 0) {
          const badge = document.createElement('span');
          badge.className = 'preview-badge';
          badge.textContent = 'Portada';
          wrap.appendChild(badge);
        }

        photoPreview.appendChild(wrap);
      };
      reader.readAsDataURL(file);
    });
  });

  // Highlight drop area on drag
  const fileUploadArea = document.getElementById('fileUploadArea');
  if (fileUploadArea) {
    fileUploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      fileUploadArea.style.borderColor = 'var(--gold)';
      fileUploadArea.style.background = 'rgba(201,168,76,0.07)';
    });

    fileUploadArea.addEventListener('dragleave', () => {
      fileUploadArea.style.borderColor = '';
      fileUploadArea.style.background = '';
    });

    fileUploadArea.addEventListener('drop', () => {
      fileUploadArea.style.borderColor = '';
      fileUploadArea.style.background = '';
    });
  }
}

// ===== FORM SUBMIT LOADING STATE =====
const form = document.getElementById('propertyForm');
const submitBtn = document.getElementById('submitBtn');

if (form && submitBtn) {
  form.addEventListener('submit', (e) => {
    // Basic check: at least one photo selected
    if (fotoInput && fotoInput.files.length === 0) {
      e.preventDefault();
      alert('Por favor, subí al menos una foto de la propiedad.');
      return;
    }

    // Show loading state
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');

    if (btnText && btnLoading) {
      btnText.style.display = 'none';
      btnLoading.style.display = 'inline-flex';
    }
    submitBtn.disabled = true;
  });
}
