    // Função para atualizar campos dependentes (médico e equipe) quando a unidade muda
    function atualizarCamposUnidade(unidade) {
        console.log("Função atualizarCamposUnidade foi chamada com unidade:", unidade);
        
        // Referências aos elementos
        const medicoSelect = document.getElementById('medico');
        const equipeContainer = document.getElementById('equipe_container');
        
        // Resetar os campos se nenhuma unidade for selecionada
        if (!unidade) {
            medicoSelect.innerHTML = '<option value="">Selecione a unidade primeiro...</option>';
            medicoSelect.disabled = true;
            equipeContainer.innerHTML = '<p class="select-message">Selecione a unidade primeiro...</p>';
            return;
        }
        
        // Mostrar estado de carregamento
        medicoSelect.innerHTML = '<option value="">Carregando médicos...</option>';
        medicoSelect.disabled = true;
        equipeContainer.innerHTML = '<p class="loading-message">Carregando equipe...</p>';
        
        // Buscar dados dos médicos
        fetch('/get_medicos/' + encodeURIComponent(unidade))
            .then(response => response.json())
            .then(data => {
                console.log("Médicos carregados:", data);
                // Atualizar select de médicos
                medicoSelect.innerHTML = '<option value="">Selecione o médico...</option>';
                data.medicos.forEach(medico => {
                    const option = document.createElement('option');
                    option.value = medico;
                    option.textContent = medico;
                    medicoSelect.appendChild(option);
                });
                medicoSelect.disabled = false;
            })
            .catch(error => {
                console.error('Erro ao carregar médicos:', error);
                medicoSelect.innerHTML = '<option value="">Erro ao carregar médicos</option>';
            });
            
        // Buscar dados da equipe
        fetch('/get_equipe/' + encodeURIComponent(unidade))
            .then(response => response.json())
            .then(data => {
                console.log("Equipe carregada:", data);
                // Atualizar checkboxes da equipe
                equipeContainer.innerHTML = '';
                data.equipe.forEach(membro => {
                    const checkboxDiv = document.createElement('div');
                    checkboxDiv.className = 'checkbox-item';
                    
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'equipe';
                    checkbox.value = membro;
                    checkbox.id = 'equipe_' + membro.replace(/\s+/g, '_');
                    
                    const label = document.createElement('label');
                    label.htmlFor = checkbox.id;
                    label.textContent = membro;
                    
                    checkboxDiv.appendChild(checkbox);
                    checkboxDiv.appendChild(label);
                    equipeContainer.appendChild(checkboxDiv);
                });
            })
            .catch(error => {
                console.error('Erro ao carregar equipe:', error);
                equipeContainer.innerHTML = '<p class="error-message">Erro ao carregar equipe</p>';
            });
    }

    // Funções para controlar campos de Body Hair
    function toggleBodyHairFields() {
        const bodyHairCheck = document.getElementById('body-hair-check');
        const bodyHairFields = document.getElementById('body-hair-fields');

        if (bodyHairCheck.checked) {
            bodyHairFields.style.display = 'block';
        } else {
            bodyHairFields.style.display = 'none';
            
            // Reset all source field checkboxes
            document.querySelectorAll('.body-hair-option input[type="checkbox"]').forEach(checkbox => {
                if (checkbox.id !== 'body-hair-check') {
                    checkbox.checked = false;
                    const sourceId = checkbox.id.split('-')[0];
                    toggleSourceFields(sourceId, false);
                }
            });
        }
    }

    function toggleSourceFields(sourceId, show) {
        const fieldsContainer = document.getElementById(`${sourceId}-fields`);
        const checkbox = document.getElementById(`${sourceId}-check`);
        
        // If show parameter is provided, use it; otherwise use checkbox status
        const shouldShow = show !== undefined ? show : checkbox.checked;
        
        if (shouldShow) {
            fieldsContainer.style.display = 'block';
        } else {
            fieldsContainer.style.display = 'none';
            
            // Clear input values when hiding
            fieldsContainer.querySelectorAll('input[type="number"]').forEach(input => {
                input.value = '';
            });
            fieldsContainer.querySelectorAll('textarea').forEach(textarea => {
                textarea.value = '';
            });
        }
    }

    function setupExtractionCalculations() {
        const quadrantes = ['q1', 'q2', 'q3', 'q4'];

        quadrantes.forEach(q => {
            const areaInput = document.getElementById(`${q}_area`);
            const furosInput = document.getElementById(`${q}_furos`);
            const fiosInput = document.getElementById(`${q}_fios`);

            if (areaInput && furosInput && fiosInput) {
                const updateCalculations = () => {
                    const area = parseFloat(areaInput.value) || 0;
                    const furos = parseFloat(furosInput.value) || 0;
                    const fios = parseFloat(fiosInput.value) || 0;

                    // Calcular densidade (furos/área) e arredondar para baixo
                    const densidade = area > 0 ? furos / area : 0;
                    document.getElementById(`${q}_densidade_result`).textContent = Math.floor(densidade);

                    // Calcular taxa de quebra ((furos-fios)/furos * 100) e arredondar para baixo
                    const taxaQuebra = furos > 0 ? ((furos - fios) / furos) * 100 : 0;
                    document.getElementById(`${q}_taxa_quebra_result`).textContent = Math.floor(taxaQuebra);
                };

                areaInput.addEventListener('input', updateCalculations);
                furosInput.addEventListener('input', updateCalculations);
                fiosInput.addEventListener('input', updateCalculations);
            }
        });
    }

    // Função para navegar entre páginas
    function goToPage(pageNumber) {
        // Se estiver indo para a página 2, validar campos obrigatórios da página 1
        if (pageNumber === 2) {
            let isValid = true;
            let missingFields = [];

            // Verificar todos os campos obrigatórios da página 1
            const requiredFields = document.querySelectorAll('#page-1 [required]');
            requiredFields.forEach(field => {
                if (!field.value) {
                    isValid = false;
                    field.classList.add('field-error');
                    const label = document.querySelector(`label[for="${field.id}"]`);
                    if (label) {
                        missingFields.push(label.textContent.replace('*', '').trim());
                    }
                } else {
                    field.classList.remove('field-error');
                }
            });

            if (!isValid) {
                alert(`Por favor, preencha os seguintes campos obrigatórios:\n- ${missingFields.join('\n- ')}`);
                return;
            }
        }

        // Ocultar todas as páginas
        document.querySelectorAll('.form-page').forEach(page => {
            page.style.display = 'none';
        });

        // Mostrar a página selecionada
        document.getElementById('page-' + pageNumber).style.display = 'block';

        // Atualizar indicadores de paginação
        document.querySelectorAll('.pagination-step').forEach(step => {
            step.classList.remove('active');
            if (parseInt(step.getAttribute('data-page')) === pageNumber) {
                step.classList.add('active');
            }
        });

        // Rolar para o topo
        window.scrollTo(0, 0);
    }

    function adjustTime(action) {
        const tempoCirurgiaInput = document.getElementById('tempo_cirurgia');
        let currentTime = parseFloat(tempoCirurgiaInput.value);

        if (action === 'add') {
            currentTime += 0.5;
        } else if (action === 'subtract') {
            currentTime -= 0.5;
            currentTime = Math.max(0, currentTime); // Prevent negative values
        }

        tempoCirurgiaInput.value = currentTime;
    }

    // Função para mostrar/ocultar campo de seringas do bloqueio
    function toggleBloqueioSeringas(value) {
        const seringasContainer = document.getElementById('bloqueio_seringas_container');
        const comentariosContainer = document.getElementById('bloqueio_comentarios_container');

        if (value === "Não") {
            seringasContainer.style.display = 'none';
            comentariosContainer.style.display = 'none';
            document.getElementById('bloqueio_seringas').value = '';
            document.getElementById('bloqueio_comentarios').value = '';
        } else {
            seringasContainer.style.display = 'block';
            comentariosContainer.style.display = 'block';
        }
    }

    // Inicializar quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOMContentLoaded disparado");
        const unidadeSelect = document.getElementById('unidade');
        if (unidadeSelect) {
            console.log("Select de unidade encontrado:", unidadeSelect);
            
            // Adicionar listener para mudanças futuras
            unidadeSelect.addEventListener('change', function() {
                console.log("Unidade alterada para:", this.value);
                atualizarCamposUnidade(this.value);
            });
            
            // Se já houver uma unidade selecionada, atualizar os campos
            if (unidadeSelect.value) {
                console.log("Unidade já selecionada:", unidadeSelect.value);
                atualizarCamposUnidade(unidadeSelect.value);
            }
        } else {
            console.log("Select de unidade não encontrado");
        }
        
        // Inicializar outros componentes
        setupExtractionCalculations();
        
        // Verificar status inicial de body hair e bloqueio
        const bodyHairCheck = document.getElementById('body-hair-check');
        if (bodyHairCheck && bodyHairCheck.checked) {
            toggleBodyHairFields();
        }
        
        const bloqueioSelect = document.getElementById('bloqueio');
        if (bloqueioSelect) {
            toggleBloqueioSeringas(bloqueioSelect.value);
        }
    });