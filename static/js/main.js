document.addEventListener('DOMContentLoaded', () => {

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMetaTag ? csrfMetaTag.getAttribute('content') : '';

    function showToast(message, level = 'danger') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = 1100;
            document.body.appendChild(container);
        }
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-bg-${level} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>`;
        container.appendChild(toastEl);
        new bootstrap.Toast(toastEl, { delay: 4000 }).show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    function updateVoteUI(button, data) {
        const container = button.closest('.input-group');
        if (!container) return;

        const ratingInput = container.querySelector('.rating-input');
        if (ratingInput && data.rating !== undefined) {
            ratingInput.value = data.rating;
        }

        const upBtn = container.querySelector('[data-action="up"]');
        const downBtn = container.querySelector('[data-action="down"]');
        if (!upBtn || !downBtn) return;

        upBtn.classList.remove('btn-success');
        upBtn.classList.add('btn-outline-success');
        downBtn.classList.remove('btn-danger');
        downBtn.classList.add('btn-outline-danger');

        if (data.user_vote === 1) {
            upBtn.classList.remove('btn-outline-success');
            upBtn.classList.add('btn-success');
        } else if (data.user_vote === -1) {
            downBtn.classList.remove('btn-outline-danger');
            downBtn.classList.add('btn-danger');
        }
    }

    async function sendVote(button) {
        if (button.disabled) return;
        const { type, id, action } = button.dataset;

        if (!csrfToken) {
            showToast('Отсутствует CSRF-токен. Перезагрузите страницу.');
            return;
        }

        const container = button.closest('.input-group');
        const groupButtons = container ? container.querySelectorAll('button.js-vote') : [button];
        groupButtons.forEach(b => (b.disabled = true));

        const formData = new FormData();
        formData.append('action', action);

        let response;
        try {
            response = await fetch(`/vote/${type}/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
        } catch (e) {
            showToast('Ошибка сети. Попробуйте ещё раз.');
            groupButtons.forEach(b => (b.disabled = false));
            return;
        }

        let data = {};
        try { data = await response.json(); } catch { /* не JSON */ }

        if (response.status === 401) {
            const loginUrl = data.login_url || '/login/';
            const next = encodeURIComponent(window.location.pathname + window.location.hash);
            if (confirm('Чтобы голосовать, нужно войти. Перейти ко входу?')) {
                window.location.href = `${loginUrl}?next=${next}`;
            }
        } else if (response.status === 403) {
            showToast('Запрос отклонён (возможно, недействителен CSRF). Перезагрузите страницу.');
        } else if (response.status === 405) {
            showToast('Неверный метод запроса.');
        } else if (response.status === 400) {
            showToast(data.error || 'Невалидные параметры запроса.');
        } else if (!response.ok) {
            showToast(data.error || `Ошибка ${response.status}.`);
        } else {
            updateVoteUI(button, data);
        }

        groupButtons.forEach(b => (b.disabled = false));
    }

    document.querySelectorAll('.js-vote').forEach(button => {
        button.addEventListener('click', e => {
            e.preventDefault();
            sendVote(button);
        });
    });

    function updateMarkCorrectUI(questionId, markedAnswerId, isCorrect) {
        // Обновляем кнопки автора у всех ответов этого вопроса:
        // правильный — заполненная btn-success, остальные — btn-outline-success.
        const buttons = document.querySelectorAll(
            `.js-mark-correct[data-question-id="${questionId}"]`
        );
        buttons.forEach(btn => {
            const isThisOne = btn.dataset.answerId === String(markedAnswerId);
            const becomesCorrect = isThisOne && isCorrect;

            btn.classList.toggle('btn-success', becomesCorrect);
            btn.classList.toggle('btn-outline-success', !becomesCorrect);
            btn.title = becomesCorrect
                ? 'Снять метку правильного ответа'
                : 'Отметить как правильный ответ';
        });

        // Подсветка карточки ответа (зелёная полоса + фон) — навешиваем/снимаем классы.
        document.querySelectorAll('[id^="answer-"]').forEach(card => {
            const cardAnswerId = card.id.replace('answer-', '');
            const becomesCorrect = cardAnswerId === String(markedAnswerId) && isCorrect;

            card.classList.toggle('bg-success', becomesCorrect);
            card.classList.toggle('bg-opacity-10', becomesCorrect);
        });
    }

    async function sendMarkCorrect(button) {
        if (button.disabled) return;
        const { questionId, answerId } = button.dataset;

        if (!csrfToken) {
            showToast('Отсутствует CSRF-токен. Перезагрузите страницу.');
            return;
        }

        button.disabled = true;

        const formData = new FormData();
        formData.append('answer_id', answerId);

        let response;
        try {
            response = await fetch(`/question/${questionId}/mark_correct/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
        } catch (e) {
            showToast('Ошибка сети. Попробуйте ещё раз.');
            button.disabled = false;
            return;
        }

        let data = {};
        try { data = await response.json(); } catch { /* не JSON */ }

        if (response.status === 401) {
            const loginUrl = data.login_url || '/login/';
            const next = encodeURIComponent(window.location.pathname + window.location.hash);
            if (confirm('Чтобы отметить правильный ответ, нужно войти. Перейти ко входу?')) {
                window.location.href = `${loginUrl}?next=${next}`;
            }
        } else if (response.status === 403) {
            showToast(data.error || 'Только автор вопроса может отмечать правильный ответ.');
        } else if (response.status === 405) {
            showToast('Неверный метод запроса.');
        } else if (response.status === 400) {
            showToast(data.error || 'Невалидные параметры запроса.');
        } else if (!response.ok) {
            showToast(data.error || `Ошибка ${response.status}.`);
        } else {
            updateMarkCorrectUI(data.question_id, data.answer_id, data.is_correct);
        }

        button.disabled = false;
    }

    document.querySelectorAll('.js-mark-correct').forEach(button => {
        button.addEventListener('click', e => {
            e.preventDefault();
            sendMarkCorrect(button);
        });
    });

    // --- Полнотекстовый поиск с debounce ---
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-dropdown');

    if (searchInput && searchDropdown) {
        let searchTimer = null;

        function closeDropdown() {
            searchDropdown.classList.add('d-none');
            searchDropdown.innerHTML = '';
        }

        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimer);
            const q = this.value.trim();

            if (q.length < 2) {
                closeDropdown();
                return;
            }

            searchTimer = setTimeout(function () {
                const url = searchInput.dataset.searchUrl + '?q=' + encodeURIComponent(q);
                fetch(url)
                    .then(r => r.json())
                    .then(function (data) {
                        searchDropdown.innerHTML = '';
                        if (data.length === 0) {
                            closeDropdown();
                            return;
                        }
                        data.forEach(function (item) {
                            const li = document.createElement('li');
                            li.className = 'list-group-item list-group-item-action p-2';
                            const a = document.createElement('a');
                            a.href = item.url;
                            a.className = 'text-decoration-none text-dark d-block text-truncate';
                            a.textContent = item.title;
                            li.appendChild(a);
                            searchDropdown.appendChild(li);
                        });
                        searchDropdown.classList.remove('d-none');
                    })
                    .catch(function () {});
            }, 300);
        });

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                closeDropdown();
            }
        });

        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeDropdown();
        });
    }
});
