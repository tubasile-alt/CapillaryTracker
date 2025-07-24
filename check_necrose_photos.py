#!/usr/bin/env python3
"""
Script para verificar e analisar fotos de necrose
Verifica integridade dos arquivos e dados no banco
"""

import os
import logging
from app import app, db, Necrose, NecrosePhoto

def check_photos_integrity():
    """Verifica integridade das fotos de necrose"""
    print("🔍 RELATÓRIO DE VERIFICAÇÃO DAS FOTOS DE NECROSE")
    print("=" * 60)
    
    with app.app_context():
        # 1. Verificar total de necroses cadastradas
        total_necroses = Necrose.query.count()
        print(f"📊 Total de necroses cadastradas: {total_necroses}")
        
        # 2. Verificar fotos no banco de dados
        photos_in_db = NecrosePhoto.query.count()
        print(f"📊 Total de fotos no banco: {photos_in_db}")
        
        # 3. Verificar arquivos físicos
        photos_dir = 'static/uploads/necrose_photos'
        if os.path.exists(photos_dir):
            physical_files = [f for f in os.listdir(photos_dir) 
                            if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != '.gitkeep']
            print(f"📊 Arquivos físicos encontrados: {len(physical_files)}")
            
            if physical_files:
                print("\n📁 Arquivos físicos:")
                for i, file in enumerate(physical_files, 1):
                    file_path = os.path.join(photos_dir, file)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    print(f"  {i}. {file} ({file_size:.1f} KB)")
        else:
            print("❌ Diretório de fotos não encontrado!")
            return
        
        # 4. Análise detalhada por necrose
        print("\n" + "=" * 60)
        print("📋 ANÁLISE POR NECROSE:")
        print("=" * 60)
        
        necroses = Necrose.query.order_by(Necrose.id).all()
        necroses_with_photos = 0
        orphaned_photos = []
        missing_photos = []
        
        for necrose in necroses:
            photos = NecrosePhoto.query.filter_by(necrose_id=necrose.id).all()
            
            if photos:
                necroses_with_photos += 1
                print(f"\n🏥 [{necrose.id}] {necrose.paciente_nome}")
                print(f"   📅 Cirurgia: {necrose.data_cirurgia}")
                print(f"   🏥 Unidade: {necrose.unidade}")
                print(f"   📷 Fotos cadastradas: {len(photos)}")
                
                for photo in photos:
                    # Verificar se arquivo existe
                    if photo.file_path:
                        file_path = photo.file_path.lstrip('/')
                    else:
                        file_path = f"static/uploads/necrose_photos/{photo.filename}"
                    
                    exists = os.path.exists(file_path)
                    status = "✅ OK" if exists else "❌ MISSING"
                    
                    if exists:
                        file_size = os.path.getsize(file_path) / 1024
                        print(f"   📎 {photo.filename} - {status} ({file_size:.1f} KB)")
                    else:
                        print(f"   📎 {photo.filename} - {status}")
                        missing_photos.append({
                            'necrose_id': necrose.id,
                            'patient': necrose.paciente_nome,
                            'filename': photo.filename,
                            'path': file_path
                        })
        
        # 5. Verificar fotos órfãs (arquivos sem registro no banco)
        print("\n" + "=" * 60)
        print("🔍 VERIFICAÇÃO DE FOTOS ÓRFÃS:")
        print("=" * 60)
        
        db_filenames = [photo.filename for photo in NecrosePhoto.query.all()]
        
        for file in physical_files:
            if file not in db_filenames:
                orphaned_photos.append(file)
                file_path = os.path.join(photos_dir, file)
                file_size = os.path.getsize(file_path) / 1024
                print(f"⚠️  {file} ({file_size:.1f} KB) - Arquivo órfão (sem registro no banco)")
        
        # 6. Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO FINAL:")
        print("=" * 60)
        print(f"✅ Necroses com fotos: {necroses_with_photos}/{total_necroses}")
        print(f"✅ Fotos no banco: {photos_in_db}")
        print(f"✅ Arquivos físicos: {len(physical_files)}")
        print(f"❌ Fotos órfãs: {len(orphaned_photos)}")
        print(f"❌ Fotos faltando: {len(missing_photos)}")
        
        # 7. Recomendações
        print("\n" + "=" * 60)
        print("💡 RECOMENDAÇÕES:")
        print("=" * 60)
        
        if missing_photos:
            print("🔧 Limpar registros de fotos que não existem fisicamente:")
            for photo in missing_photos:
                print(f"   DELETE FROM necrose_photo WHERE filename = '{photo['filename']}';")
        
        if orphaned_photos:
            print("\n🔧 Associar fotos órfãs ou removê-las:")
            for file in orphaned_photos:
                print(f"   Verificar manualmente: {file}")
        
        if not missing_photos and not orphaned_photos and photos_in_db > 0:
            print("🎉 Todas as fotos estão íntegras e bem organizadas!")
        
        if photos_in_db == 0:
            print("⚠️  Nenhuma foto encontrada. Considere adicionar fotos de exemplo.")

if __name__ == "__main__":
    check_photos_integrity()